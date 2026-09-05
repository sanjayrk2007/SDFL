import os
import csv
import matplotlib.pyplot as plt

def plot_e10(results_dir):
    try:
        data = []
        with open(os.path.join(results_dir, "E10_results.csv"), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        data.sort(key=lambda x: float(x["window_seconds"]))
        
        windows = [float(x["window_seconds"]) for x in data]
        accepted = [1 if x["legitimate_accepted"] == "True" else 0 for x in data]
        p95 = float(data[0]["p95_latency"])
        
        plt.figure(figsize=(10, 6))
        plt.plot(windows, accepted, 'bo-', label="Legitimate Accepted")
        plt.axvline(x=p95, color='r', linestyle='--', label="p95 Latency")
        plt.xlabel("Temporal Window (seconds)")
        plt.ylabel("Acceptance (1=Yes, 0=No)")
        plt.title("E10: Temporal Window vs Legitimate Acceptance")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(results_dir, "E10_temporal_window.png"))
        plt.close()
    except Exception as e:
        print(f"Error plotting E10: {e}")

def plot_e14(results_dir):
    try:
        data = []
        with open(os.path.join(results_dir, "E14_results.csv"), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
                
        data.sort(key=lambda x: int(x["num_clients"]))
        
        clients = [int(x["num_clients"]) for x in data]
        server_time = [float(x["server_val_time"]) + float(x["server_dec_time"]) + float(x["server_key_dest_time"]) for x in data]
        client_train = [float(x["client_train_time_mean"]) for x in data]
        total_rx = [float(x["total_rx_bytes"]) / 1024 / 1024 for x in data]
        client_mem = [float(x["client_memory_mean"]) / 1024 / 1024 for x in data]
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
        
        # Timing
        ax1.plot(clients, server_time, 'ro-', label="Server Overhead")
        ax1.plot(clients, client_train, 'bo-', label="Client Train Mean")
        ax1.set_xlabel("Number of Clients")
        ax1.set_ylabel("Time (s)")
        ax1.set_title("E14: Scalability Time")
        ax1.legend()
        
        # Communication
        ax2.plot(clients, total_rx, 'go-', label="Total RX (MB)")
        ax2.set_xlabel("Number of Clients")
        ax2.set_ylabel("Megabytes")
        ax2.set_title("E14: Communication Volume")
        ax2.legend()
        
        # Memory
        ax3.plot(clients, client_mem, 'mo-', label="Client Mem (MB)")
        ax3.set_xlabel("Number of Clients")
        ax3.set_ylabel("Megabytes")
        ax3.set_title("E14: Client Memory")
        ax3.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "E14_scalability.png"))
        plt.close()
    except Exception as e:
        print(f"Error plotting E14: {e}")

def process_e15(results_dir):
    try:
        with open(os.path.join(results_dir, "E15_results.csv"), 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
            
        with open(os.path.join(results_dir, "E15_robustness_table.md"), "w") as f:
            f.write("# E15 Fault Robustness Table\n\n")
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
            for row in rows:
                f.write("| " + " | ".join(row) + " |\n")
    except Exception as e:
        print(f"Error processing E15: {e}")

if __name__ == "__main__":
    os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), 'scratch')
    os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)
    plot_e10("results")
    plot_e14("results")
    process_e15("results")


