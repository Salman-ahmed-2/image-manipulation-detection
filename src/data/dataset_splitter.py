"""Group-aware dataset partitioning utilities."""

from __future__ import annotations

import math

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from config import Config


def verify_no_leakage(split_df: pd.DataFrame, group_col: str = "group_id") -> bool:
	"""Assert that each group occurs in only one split partition.

	Args:
		split_df: Metadata containing group and split columns.
		group_col: Column containing donor group identifiers.

	Returns:
		True when no group spans multiple splits.

	Raises:
		ValueError: If either required column is missing.
		AssertionError: If a group occurs in multiple split partitions.
	"""
	required_columns = {group_col, "split"}
	missing_columns = required_columns.difference(split_df.columns)
	if missing_columns:
		missing = ", ".join(sorted(missing_columns))
		raise ValueError(f"Required split dataframe columns are missing: {missing}.")

	split_count_by_group = split_df.groupby(group_col, dropna=False)["split"].nunique(
		dropna=False
	)
	leaking_groups = split_count_by_group[split_count_by_group > 1].index.tolist()
	if leaking_groups:
		raise AssertionError(f"Groups appear in multiple dataset splits: {leaking_groups}")
	return True


class DatasetSplitter:
	"""Partition image metadata by donor group to prevent split leakage."""

	def __init__(
		self,
		train_ratio: float = Config.DATASET_TRAIN_RATIO,
		val_ratio: float = Config.DATASET_VALIDATION_RATIO,
		test_ratio: float = Config.DATASET_TEST_RATIO,
		random_state: int = Config.RANDOM_SEED,
	) -> None:
		"""Initialize split ratios and reproducibility settings.

		Args:
			train_ratio: Fraction of groups assigned to training.
			val_ratio: Fraction of groups assigned to validation.
			test_ratio: Fraction of groups assigned to testing.
			random_state: Seed passed to each group shuffle split.

		Raises:
			ValueError: If any ratio is non-positive or ratios do not sum to one.
		"""
		ratios = (train_ratio, val_ratio, test_ratio)
		if any(not math.isfinite(ratio) or ratio <= 0 for ratio in ratios):
			raise ValueError("Dataset split ratios must be finite and greater than zero.")
		if not math.isclose(sum(ratios), 1.0):
			raise ValueError("Dataset split ratios must sum to 1.0.")

		self.train_ratio = train_ratio
		self.val_ratio = val_ratio
		self.test_ratio = test_ratio
		self.random_state = random_state

	def split_dataframe(self, df: pd.DataFrame, group_col: str = "group_id") -> pd.DataFrame:
		"""Split rows into train, validation, and test partitions by group.

		The first GroupShuffleSplit reserves the configured training fraction.
		A second split divides the remaining groups according to the relative
		validation and test ratios.

		Args:
			df: Metadata rows containing a donor group identifier.
			group_col: Column containing donor group identifiers.

		Returns:
			A copy of ``df`` with a ``split`` column.

		Raises:
			ValueError: If required group data is missing or too few groups exist.
		"""
		if group_col not in df.columns:
			raise ValueError(f"Group column '{group_col}' is missing from the dataframe.")
		if df.empty:
			raise ValueError("Cannot split an empty dataframe.")
		if df[group_col].isna().any():
			raise ValueError(f"Group column '{group_col}' contains missing values.")

		group_count = df[group_col].nunique()
		if group_count < Config.DATASET_MINIMUM_GROUPS:
			raise ValueError(
				"At least four distinct groups are required to create non-empty train, "
				"validation, and test splits."
			)

		train_indices, temporary_indices = next(
			GroupShuffleSplit(
				n_splits=1,
				train_size=self.train_ratio,
				random_state=self.random_state,
			).split(df, groups=df[group_col])
		)
		temporary_df = df.iloc[temporary_indices]
		validation_fraction = self.val_ratio / (self.val_ratio + self.test_ratio)
		validation_indices, test_indices = next(
			GroupShuffleSplit(
				n_splits=1,
				train_size=validation_fraction,
				random_state=self.random_state,
			).split(temporary_df, groups=temporary_df[group_col])
		)

		train_name, validation_name, test_name = Config.DATASET_SPLIT_NAMES
		split_labels = pd.Series(index=range(len(df)), dtype="object")
		split_labels.iloc[train_indices] = train_name
		split_labels.iloc[temporary_indices[validation_indices]] = validation_name
		split_labels.iloc[temporary_indices[test_indices]] = test_name

		split_df = df.copy()
		split_df["split"] = split_labels.to_numpy()
		self.verify_no_leakage(split_df, group_col)
		return split_df

	@staticmethod
	def verify_no_leakage(split_df: pd.DataFrame, group_col: str = "group_id") -> bool:
		"""Delegate the group isolation assertion to the module utility.

		Args:
			split_df: Metadata containing group and split columns.
			group_col: Column containing donor group identifiers.

		Returns:
			True when the module-level verification succeeds.

		Raises:
			ValueError: If either required column is missing.
			AssertionError: If a group occurs in multiple split partitions.
		"""
		return verify_no_leakage(split_df, group_col)
