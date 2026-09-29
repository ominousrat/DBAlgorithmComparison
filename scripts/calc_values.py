from src.common.csv_handler import read_data
from src.common.evaluator import Evaluator
from pathlib import Path
from src.benchmarks.config import AppConfig

folder = Path("results")
csv_paths = [path for path in folder.rglob("*.csv") if path.is_file()]

evaluator = Evaluator()

logging = True

config = AppConfig.from_env("results")

result = []

for path in csv_paths:
    data = read_data(path)

    if "memory" in str(path):
        data = [row[2] for row in data]
        data = evaluator.sort_list(data)

        range_indices = evaluator.get_range_indices(
            [float(row) for row in data],
            config.lower_fraction,
            config.upper_fraction,
        )

        calculated_average_and_bounds = evaluator.calculate_average_and_bounds(
            [float(row) for row in data],
            range_indices[0],
            range_indices[1],
        )
        if logging:
            print(path)
            print(f"{config.lower_fraction * 100}%: {calculated_average_and_bounds.lower_bound}mib")
            print(f"avg:   {calculated_average_and_bounds.average}mib")
            print(f"{config.upper_fraction * 100}%: {calculated_average_and_bounds.upper_bound}mib\n")
        
        result.append(str(path))
        result.append(f"{config.lower_fraction * 100}%: {calculated_average_and_bounds.lower_bound}mib")
        result.append(f"avg:   {calculated_average_and_bounds.average}mib")
        result.append(f"{config.upper_fraction * 100}%: {calculated_average_and_bounds.upper_bound}mib")
        result.append("\n")

    else:
        range_indices = evaluator.get_range_indices(
            [float(row[0]) for row in data],
            config.lower_fraction,
            config.upper_fraction,
        )
        
        calculated_average_and_bounds = evaluator.calculate_average_and_bounds(
            [float(row[0]) for row in data],
            range_indices[0],
            range_indices[1],
        )

        if logging:
            print(path)
            print(f"{config.lower_fraction * 100}%: {calculated_average_and_bounds.lower_bound}μs")
            print(f"avg:   {calculated_average_and_bounds.average}μs")
            print(f"{config.upper_fraction * 100}%: {calculated_average_and_bounds.upper_bound}μs\n")
        
        result.append(str(path))
        result.append(f"{config.lower_fraction * 100}%: {calculated_average_and_bounds.lower_bound}μs")
        result.append(f"avg:   {calculated_average_and_bounds.average}μs")
        result.append(f"{config.upper_fraction * 100}%: {calculated_average_and_bounds.upper_bound}μs")
        result.append("\n")

    

report = "\n".join(result)
Path("results/calculated_results.txt").write_text(report, encoding="utf-8")