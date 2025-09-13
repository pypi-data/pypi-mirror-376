from dqu.base import BaseDQCheck
from dqu.kernel.engine_runner import EngineRunner
from dqu.utils.exceptions import ColumnNotFoundException
from dqu.utils.config_validator import ConfigValidator

class DquDupCheck(BaseDQCheck):
    """
    Duplicate Check Rule:
    Checks for duplicate rows based on specified columns.
    Supports Pandas, Spark DataFrames, Flink and Ray.

    Example config:
    {
        "columns": ["id", "email"]
    }
    """

    def run(self, evaluation="basic"):
        ConfigValidator.validate(self.config, self.expected_config())
        columns = self.config.get("columns")
        if not columns:
            raise ValueError("'columns' must be specified in the config.")

        df = self.qdf.get_df()
        engine = self.qdf.get_engine()
        if engine not in {"ray", "flink"}:
            for col in columns:
                if col not in df.columns:
                    raise ColumnNotFoundException(col)
        # Pass columns for flink, else None
        columns_arg = self.qdf.columns if engine in {"flink"} else None
        runner = EngineRunner(df, engine, run_id=self.run_id, columns=columns_arg)
        return runner.run_dup_check(columns, evaluation=evaluation)
    
    @classmethod
    def expected_config(cls):
        return {
            "columns": (list, True)  # Required: List of column names to check for duplicates
        }