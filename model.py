import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        )
        self.skip = (
            nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
            if in_channels != out_channels
            else nn.Identity()
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.conv_block(x) + self.skip(x))


class SEBlock(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        b, c, _, _ = x.shape
        scale = self.pool(x).view(b, c)
        scale = self.fc(scale).view(b, c, 1, 1)
        return x * scale


class ASPPModule(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.branches = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=rate, dilation=rate, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            )
            for rate in [1, 6, 12, 18]
        ])
        self.project = nn.Conv2d(out_channels * 4, out_channels, kernel_size=1, bias=False)

    def forward(self, x):
        return self.project(torch.cat([branch(x) for branch in self.branches], dim=1))


class ResUNetPlusPlus(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder1 = ResidualBlock(3, 32)
        self.encoder2 = ResidualBlock(32, 64)
        self.encoder3 = ResidualBlock(64, 128)
        self.encoder4 = ResidualBlock(128, 256)

        self.pool = nn.MaxPool2d(2)

        self.bridge = ASPPModule(256, 256)

        self.se1 = SEBlock(32)
        self.se2 = SEBlock(64)
        self.se3 = SEBlock(128)
        self.se4 = SEBlock(256)

        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        self.decoder4 = ResidualBlock(256 + 256, 256)
        self.decoder3 = ResidualBlock(256 + 128, 128)
        self.decoder2 = ResidualBlock(128 + 64, 64)
        self.decoder1 = ResidualBlock(64 + 32, 32)

        self.output_head = nn.Sequential(
            nn.Conv2d(32, 1, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        e1 = self.encoder1(x)
        e2 = self.encoder2(self.pool(e1))
        e3 = self.encoder3(self.pool(e2))
        e4 = self.encoder4(self.pool(e3))

        bridge = self.bridge(self.pool(e4))

        s4 = self.se4(e4)
        d4 = self.decoder4(torch.cat([self.upsample(bridge), s4], dim=1))

        s3 = self.se3(e3)
        d3 = self.decoder3(torch.cat([self.upsample(d4), s3], dim=1))

        s2 = self.se2(e2)
        d2 = self.decoder2(torch.cat([self.upsample(d3), s2], dim=1))

        s1 = self.se1(e1)
        d1 = self.decoder1(torch.cat([self.upsample(d2), s1], dim=1))

        return self.output_head(d1)


if __name__ == "__main__":
    model = ResUNetPlusPlus()
    x = torch.randn(2, 3, 256, 256)
    out = model(x)
    print(out.shape)  # expected: torch.Size([2, 1, 256, 256])
