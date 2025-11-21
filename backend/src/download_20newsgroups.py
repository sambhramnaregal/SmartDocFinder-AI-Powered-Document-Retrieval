"""Download the 20 Newsgroups dataset and export it as .txt files.

This is an optional helper so you can quickly populate `data/docs` with
100–200+ documents grouped by category, as suggested in the assignment.
"""

import argparse
from pathlib import Path

from sklearn.datasets import fetch_20newsgroups


def export_20newsgroups(out_dir: Path, subset: str = "train") -> None:
  out_dir.mkdir(parents=True, exist_ok=True)
  dataset = fetch_20newsgroups(subset=subset, remove=("headers", "footers", "quotes"))

  print(f"Fetched 20 Newsgroups subset='{subset}' with {len(dataset.data)} posts")

  for i, (text, target) in enumerate(zip(dataset.data, dataset.target)):
    category = dataset.target_names[target]
    cat_dir = out_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    filename = cat_dir / f"doc_{i:05d}.txt"
    filename.write_text(text, encoding="utf-8", errors="ignore")

  print(f"Exported posts as .txt files under {out_dir}")


def main() -> None:
  parser = argparse.ArgumentParser(description="Download and export 20 Newsgroups as .txt files")
  parser.add_argument(
    "--out-dir",
    type=str,
    required=True,
    help="Output directory for .txt files (e.g. ../data/docs)",
  )
  parser.add_argument(
    "--subset",
    type=str,
    default="train",
    choices=["train", "test", "all"],
    help="Which 20 Newsgroups subset to download (default: train)",
  )
  args = parser.parse_args()
  out_dir = Path(args.out_dir).resolve()
  export_20newsgroups(out_dir=out_dir, subset=args.subset)


if __name__ == "__main__":
  main()


