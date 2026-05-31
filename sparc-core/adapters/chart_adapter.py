import matplotlib.pyplot as plt
import numpy as np

from ports.output_port import OutputPort


class ChartAdapter(OutputPort):
    def display_consumption(self, data: dict) -> None:
        devices = data["devices"]
        names = [d["name"] for d in devices]
        values = [d["monthly_kwh"] for d in devices]

        fig, ax = plt.subplots(figsize=(max(6, len(names) * 1.2), 5))
        bars = ax.bar(names, values, color="#4C72B0")

        ax.set_title(f'Consumo Mensal — {data["scenario"]}')
        ax.set_ylabel("Consumo (kWh/mês)")
        ax.set_xlabel("Dispositivo")

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        return fig

    def display_comparison(self, comparison: dict) -> None:
        s1 = comparison["scenario_1"]
        s2 = comparison["scenario_2"]

        names_s1 = {d["name"]: d["monthly_kwh"] for d in s1["devices"]}
        names_s2 = {d["name"]: d["monthly_kwh"] for d in s2["devices"]}
        all_names = list(names_s1.keys() | names_s2.keys())

        values_s1 = [names_s1.get(n, 0) for n in all_names]
        values_s2 = [names_s2.get(n, 0) for n in all_names]

        x = np.arange(len(all_names))
        width = 0.35

        fig, ax = plt.subplots(figsize=(max(6, len(all_names) * 1.5), 5))
        bars1 = ax.bar(x - width / 2, values_s1, width, label=s1["scenario"], color="#4C72B0")
        bars2 = ax.bar(x + width / 2, values_s2, width, label=s2["scenario"], color="#55A868")

        ax.set_title(
            f'Comparação: {s1["scenario"]} vs {s2["scenario"]}\n'
            f'Economia: {comparison["difference_kwh"]:.2f} kWh/mês '
            f'({comparison["savings_percent"]:.1f}%)'
        )
        ax.set_ylabel("Consumo (kWh/mês)")
        ax.set_xticks(x)
        ax.set_xticklabels(all_names, rotation=30, ha="right")
        ax.legend()

        for bars in (bars1, bars2):
            for bar in bars:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    f"{bar.get_height():.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        plt.tight_layout()
        return fig
