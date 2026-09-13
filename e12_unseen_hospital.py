"""E12: reproducible synthetic leave-one-client-out generalization.

The clients are overlapping, size-biased assignments rather than real hospitals.
Each fold starts from a seeded random model and excludes every record assigned to
the held-out client from remaining-client training and seen-client evaluation.
"""
import argparse, gc, json, random, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
import torch.optim as optim
from scipy.ndimage import distance_transform_edt
from torch.utils.data import ConcatDataset, DataLoader
from e2_server import DEVICE, DiceBCELoss, ResUNetPlusPlus, get_parameters, set_parameters
from e4_dpsgd import fix_model_for_opacus
from scripts.dataset import KvasirSegDataset

ROOT = Path(__file__).resolve().parent; RESULTS = ROOT / "results"
OUT_JSON, OUT_LOG, OUT_REPORT = RESULTS / "e12_unseen_results.json", RESULTS / "e12_unseen_log.jsonl", ROOT / "E12_RESULTS.md"
FOLDS = (("A", (0, 1), 2, "large+medium"), ("B", (0, 2), 1, "medium"), ("C", (1, 2), 0, "small"))
METRICS = ("dice", "iou", "precision", "recall", "hd95")

def seed(seed): random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
def log(event, **data):
    data.update(event=event, timestamp=datetime.now(timezone.utc).isoformat())
    with OUT_LOG.open("a", encoding="utf-8") as f: f.write(json.dumps(data, sort_keys=True) + "\n")
def dataset(split, client, exclude=()):
    ds = KvasirSegDataset(split=split, hospital_id=client); before = len(ds.stems)
    ds.stems = [s for s in ds.stems if s not in set(exclude)]
    return ds, before - len(ds.stems)
def hd95(p, y):
    if not p.any() and not y.any(): return 0.0
    diag = float(np.hypot(*p.shape))
    if not p.any() or not y.any(): return diag
    return float(max(np.percentile(distance_transform_edt(~y)[p], 95), np.percentile(distance_transform_edt(~p)[y], 95)))
def metrics(prob, target):
    p, y = prob > .5, target > .5; i, ps, ys, e = (p & y).sum(), p.sum(), y.sum(), 1e-7
    return {"dice":float((2*i+e)/(ps+ys+e)), "iou":float((i+e)/(ps+ys-i+e)), "precision":float((i+e)/(ps+e)), "recall":float((i+e)/(ys+e)), "hd95":hd95(p,y)}
def evaluate(model, ds):
    out = {m:[] for m in METRICS}; model.eval()
    with torch.no_grad():
        for image, mask, _ in DataLoader(ds, batch_size=1, shuffle=False, num_workers=0):
            row = metrics(model(image.to(DEVICE))[0,0].cpu().numpy(), mask[0,0].numpy())
            for k, v in row.items(): out[k].append(v)
    return {k:float(np.mean(v)) if v else None for k,v in out.items()}
def train_round(global_model, sets, a):
    reference = {k:v.detach().cpu().clone() for k,v in global_model.state_dict().items()}; updates=[]; counts=[]
    for ds in sets:
        model = ResUNetPlusPlus().to(DEVICE); fix_model_for_opacus(model); model.load_state_dict(reference)
        opt = optim.Adam(model.parameters(), lr=a.lr); loss_fn=DiceBCELoss(); model.train()
        for _ in range(a.local_epochs):
            for image, mask, _ in DataLoader(ds, batch_size=a.batch_size, shuffle=True, drop_last=False, num_workers=0):
                opt.zero_grad(); loss=loss_fn(model(image.to(DEVICE)), mask.to(DEVICE)); loss.backward(); opt.step()
        updates.append(get_parameters(model)); counts.append(len(ds)); del model, opt
    total=sum(counts); set_parameters(global_model, [sum(u[i]*n/total for u,n in zip(updates,counts)) for i in range(len(updates[0]))]); gc.collect()
def run_fold(name, clients, held, bias, a, held_stems):
    train, removed_train = zip(*(dataset("train", c, held_stems) for c in clients))
    seen, removed_seen = zip(*(dataset("test", c, held_stems) for c in clients))
    held_test, _ = dataset("test", held)
    training_stems=set().union(*(set(x.stems) for x in train))
    assert not training_stems & held_stems and not training_stems & set(held_test.stems)
    seed(a.seed+held); model=ResUNetPlusPlus().to(DEVICE); fix_model_for_opacus(model)
    init_sum=float(sum(p.detach().float().sum().cpu() for p in model.parameters())); started=time.perf_counter()
    for rnd in range(1,a.rounds+1): train_round(model,train,a); log("round_complete",fold=name,round=rnd)
    seen_m, held_m=evaluate(model,ConcatDataset(list(seen))),evaluate(model,held_test)
    row={"fold":name,"train_clients":list(clients),"held_out_client":held,"held_out_bias":bias,"train_samples":[len(x) for x in train],"held_out_test_samples":len(held_test),"removed_overlapping_train_records":list(removed_train),"removed_overlapping_seen_test_records":list(removed_seen),"initialization":"seeded_random_no_checkpoint","initial_parameter_sum":init_sum,"training_seconds":time.perf_counter()-started,"seen_client_test":seen_m,"held_out_client_test":held_m,"seen_minus_held_out":{k:seen_m[k]-held_m[k] for k in METRICS}}
    log("fold_complete",fold=name,held_out_client=held,held_out_dice=held_m["dice"]); return row
def write_report(payload):
    rows=payload["folds"]; macro={k:float(np.mean([r["held_out_client_test"][k] for r in rows])) for k in METRICS}; worst={k:(min if k!="hd95" else max)(r["held_out_client_test"][k] for r in rows) for k in METRICS}; payload["held_out_macro_mean"],payload["held_out_worst_client"]=macro,worst
    lines=["# E12 — Synthetic Leave-One-Client-Out Generalization","","> This is **not** true unseen-hospital generalization: repository clients are synthetic, size-biased, overlapping source-record assignments.","","## Protocol","","Each fold initializes a model from a reproducible random seed; no pretrained checkpoint is loaded. All records assigned to the held-out client are removed from the remaining clients' training and seen-test datasets. Hyperparameters are fixed before running; no held-out-client model selection, threshold tuning, or validation occurs.","","| Fold | Train | Held-out | Seen Dice | Held-out Dice | IoU | Precision | Recall | HD95 |","|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        s,o=r["seen_client_test"],r["held_out_client_test"]; lines.append(f"| {r['fold']} | C{r['train_clients'][0]}+C{r['train_clients'][1]} | C{r['held_out_client']} | {s['dice']:.4f} | {o['dice']:.4f} | {o['iou']:.4f} | {o['precision']:.4f} | {o['recall']:.4f} | {o['hd95']:.2f} |")
    lines += ["","## Held-out summary","","| Statistic | Dice | IoU | Precision | Recall | HD95 |","|---|---:|---:|---:|---:|---:|","| Macro mean | "+" | ".join(f"{macro[k]:.4f}" if k!="hd95" else f"{macro[k]:.2f}" for k in METRICS)+" |","| Worst client | "+" | ".join(f"{worst[k]:.4f}" if k!="hd95" else f"{worst[k]:.2f}" for k in METRICS)+" |","","## Limitation","","Record-level exclusion prevents held-out-client training exposure, but cannot make these simulated, overlapping assignments equivalent to independently collected hospital cohorts."]
    OUT_REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--rounds",type=int,default=20); p.add_argument("--local-epochs",type=int,default=1); p.add_argument("--batch-size",type=int,default=8); p.add_argument("--lr",type=float,default=1e-4); p.add_argument("--seed",type=int,default=42); a=p.parse_args(); RESULTS.mkdir(exist_ok=True); OUT_LOG.unlink(missing_ok=True)
    h=json.loads((ROOT/"hospital_splits.json").read_text(encoding="utf-8"))["hospitals"]; sets={int(k):set(v["filenames"]) for k,v in h.items()}
    payload={"experiment":"E12 synthetic leave-one-client-out generalization","completed_at":None,"config":vars(a),"device":str(DEVICE),"protocol":{"pretrained_checkpoint_used":False,"all_held_out_assignments_excluded":True,"synthetic_clients":True},"folds":[]}
    for fold in FOLDS: payload["folds"].append(run_fold(*fold,a,sets[fold[2]]))
    payload["completed_at"]=datetime.now(timezone.utc).isoformat(); write_report(payload); OUT_JSON.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps({"macro":payload["held_out_macro_mean"],"worst":payload["held_out_worst_client"]},indent=2))
if __name__ == "__main__": main()
