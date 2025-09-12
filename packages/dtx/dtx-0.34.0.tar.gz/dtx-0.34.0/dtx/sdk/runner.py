"""
High-level SDK interface for red-team evaluations (builder edition).

Quick demo
----------
from dtx.sdk.runner import DtxRunner, DtxRunnerConfigBuilder
from dtx.plugins.providers.dummy.echo import EchoAgent   # toy agent

cfg = (
    DtxRunnerConfigBuilder()
      .agent(EchoAgent())
      .max_prompts(5)
      .save_yaml("report.yaml")
       .save_json("report.json")
      .save_html("report.html")
      .build()              # no plan / plan_file / dataset supplied
)

report = DtxRunner(cfg).run()
print(report.json(indent=2))
"""

from __future__ import annotations

from typing import List, Optional
import yaml
from pathlib import Path
from loguru import logger as logger
from pydantic import Field
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from dtx.cli.runner import RedTeamTestRunner
from dtx.cli.planner import RedTeamPlanGenerator, PlanInput
from dtx.cli.scoping import RedTeamScopeCreator, ScopeInput
from dtx.cli.console_output import BaseResultCollector
from dtx.plugins.providers.base.agent import BaseAgent

from dtx_models.analysis import RedTeamPlan, PromptDataset
from dtx_models.evaluator import EvaluatorInScope
from dtx_models.results import EvalReport
from dtx_models.tactic import PromptMutationTactic
from dtx_models.providers.base import ProviderType
from dtx.cli.providers import ProviderFactory
from dtx.core.reports.html.generator import ReportGenerator as HTMLReportGenerator
from dtx.cli.runner import RedTeamRunnerInput 


# --------------------------------------------------------------------------- #
#  Fallback / dummy collector                                                 #
# --------------------------------------------------------------------------- #

class _NullCollector(BaseResultCollector):
    """No-op collector used when the user does not supply one."""
    def __init__(self) -> None:
        self.results: list = []

    def add_result(self, result) -> None:   # noqa: ANN001
        self.results.append(result)

    def finalize(self) -> None:             # noqa: D401
        pass


# --------------------------------------------------------------------------- #
#  CONFIG DATA CLASS                                                          #
# --------------------------------------------------------------------------- #

class DtxRunnerConfig(BaseModel):
    """
    Immutable configuration consumed by `DtxRunner`.
    Prefer using `DtxRunnerConfigBuilder()` to construct it fluently.
    """
    # --- mandatory ---
    agent: BaseAgent

    # --- optional ---
    collector: Optional[BaseResultCollector] = None
    plan: Optional[RedTeamPlan] = None
    plan_file: Optional[str] = None
    dataset: PromptDataset = PromptDataset.HF_JAILBREAKV  
    plugins: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None

    tactics: Optional[List[PromptMutationTactic]] = None
    evaluator: Optional[EvaluatorInScope] = None

    # Test Cases size
    max_prompts: int = 20
    max_prompts_per_plugin: int = 100
    max_goals_per_plugin: int = 10
    samples_per_prompt: int = 1

    # Concurrency
    threads: int = Field(default=1, ge=1, le=1, description="Number of threads to use. Currently fixed to 1.")

    save_yaml_path: Optional[str] = None
    save_json_path: Optional[str] = None
    save_html_path: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _validate(cls, values):
        # If both plan and plan_file are empty, dataset *always* has a value (default),
        # so the config is valid.
        return values


# --------------------------------------------------------------------------- #
#  CONFIG BUILDER                                                             #
# --------------------------------------------------------------------------- #


class DtxRunnerConfigBuilder:
    """
    Fluent builder for creating a `DtxRunnerConfig` instance.

    This builder uses a fluent interface (method chaining) to construct a complex
    configuration object step-by-step. It provides sensible defaults and validates
    the final configuration upon calling the `build()` method.
    """

    def __init__(self) -> None:
        """Initializes a new, empty DtxRunnerConfigBuilder."""
        self._data: dict = {}

    # ---------- required --------- #
    def agent(self, agent: BaseAgent) -> "DtxRunnerConfigBuilder":
        """
        Sets the agent to be tested directly from a pre-instantiated object.

        Args:
            agent (BaseAgent): A pre-instantiated and configured agent object that
                will be the target of the test run.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["agent"] = agent
        return self

    def agent_from_provider(
        self,
        provider_type: ProviderType,
        url: str = "",
        load_env_vars: bool = False,
        env_vars: Optional[dict] = None,
    ) -> "DtxRunnerConfigBuilder":
        """
        Creates and sets an agent using the ProviderFactory.

        This is a convenience method that constructs the agent from provider details,
        handling configuration and initialization internally.

        Args:
            provider_type (ProviderType): An enum value specifying the provider
                (e.g., `ProviderType.OPENAI`, `ProviderType.GEMINI`).
            url (str): The model name or endpoint identifier for the provider
                (e.g., 'gpt-4o', 'gemini-1.5-pro').
            load_env_vars (bool): If True, the provider configuration will
                automatically load credentials (like API keys) and endpoints
                from system environment variables.
            env_vars (dict, optional): A dictionary of configuration values to
                apply. Keys can be attribute names ('api_key', 'endpoint') or
                environment variable names ('OPENAI_API_KEY'). These values
                take precedence over system environment variables.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.

        Raises:
            Exception: If the agent is created but is not available, typically
                due to missing API keys or other essential configuration.
        """
        # Create a minimal RedTeamScope required for agent initialization
        scope = RedTeamScopeCreator(
            ScopeInput(description="Builder-generated provider scope")
        ).run()

        # Use ProviderFactory to initialize provider-specific config + agent
        agent = ProviderFactory(load_env_vars=load_env_vars).get_agent(
            scope=scope,
            provider_type=provider_type,
            url=url,
            env_vars=env_vars,
        )

        # Safety check: agent may be invalid if required env vars are missing
        if not agent.is_available():
            raise Exception("Agent is not available. Set required API keys or endpoints.")

        self._data["agent"] = agent
        return self


    # ---------- plan selection ---- #
    def plan(self, plan: RedTeamPlan) -> "DtxRunnerConfigBuilder":
        """
        Sets the testing strategy using a RedTeamPlan object.

        Args:
            plan (RedTeamPlan): A `RedTeamPlan` object that defines the scope,
                tactics, and goals of the test run.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["plan"] = plan
        return self

    def plan_file(self, path: str) -> "DtxRunnerConfigBuilder":
        """
        Sets the testing strategy from a YAML or JSON plan file.

        Args:
            path (str): The file path to a plan file.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["plan_file"] = path
        return self

    def dataset(self, ds: PromptDataset) -> "DtxRunnerConfigBuilder":
        """
        Sets the dataset of prompts to be used in the test run.

        Args:
            ds (PromptDataset): A `PromptDataset` object or enum value specifying
                the source of the prompts.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["dataset"] = ds
        return self

    # ---------- optional overrides #
    def collector(self, collector: BaseResultCollector) -> "DtxRunnerConfigBuilder":
        """
        Sets a custom collector for processing test results.

        Args:
            collector (BaseResultCollector): A custom result collector instance.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["collector"] = collector
        return self

    def tactics(self, tactics: List[PromptMutationTactic]) -> "DtxRunnerConfigBuilder":
        """
        Sets a list of prompt mutation tactics to apply.

        Args:
            tactics (List[PromptMutationTactic]): A list of tactics for
                programmatically altering prompts during the run.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["tactics"] = tactics
        return self

    def plugins(self, expressions: List[str]) -> "DtxRunnerConfigBuilder":
        """
        Sets the security plugins to be enabled for the run.

        Args:
            expressions (List[str]): A list of plugin names or expressions to
                enable (e.g., ['pii', 'jailbreak', 'secrets']).

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["plugins"] = expressions
        return self

    def frameworks(self, expressions: List[str]) -> "DtxRunnerConfigBuilder":
        """
        Sets the security frameworks to map results against.

        Args:
            expressions (List[str]): A list of framework identifiers to use for
                categorizing results (e.g., ['mitre-atlas', 'owasp-llm-top-10']).

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["frameworks"] = expressions
        return self

    def evaluator(self, evaluator: EvaluatorInScope) -> "DtxRunnerConfigBuilder":
        """
        Sets a custom evaluator for scoring agent responses.

        Args:
            evaluator (EvaluatorInScope): A custom evaluator object.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["evaluator"] = evaluator
        return self

    # ---------- execution limits --- #
    def max_prompts(self, n: int) -> "DtxRunnerConfigBuilder":
        """
        Sets the maximum total number of prompts to execute.

        Args:
            n (int): The maximum number of prompts for the entire run.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["max_prompts"] = n
        return self

    def max_prompts_per_plugin(self, n: int) -> "DtxRunnerConfigBuilder":
        """
        Sets the maximum number of prompts to run for each enabled plugin.

        Args:
            n (int): The prompt limit per plugin.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["max_prompts_per_plugin"] = n
        return self

    def max_goals_per_plugin(self, n: int) -> "DtxRunnerConfigBuilder":
        """
        Sets the maximum number of goals to test for each plugin.

        Args:
            n (int): The goal limit per plugin.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["max_goals_per_plugin"] = n
        return self

    def samples_per_prompt(self, n: int) -> "DtxRunnerConfigBuilder":
        """
        Sets the number of times each prompt should be sent to the agent.

        Args:
            n (int): The number of response samples to generate per prompt.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["samples_per_prompt"] = n
        return self

    def threads(self, n: int) -> "DtxRunnerConfigBuilder":
        """
        Sets the number of parallel threads for execution.

        Args:
            n (int): The number of worker threads to use.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["threads"] = n
        return self

    # ---------- output paths -------- #
    def save_yaml(self, path: str) -> "DtxRunnerConfigBuilder":
        """
        Sets the output file path for the results in YAML format.

        Args:
            path (str): The file path where the YAML report will be saved.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["save_yaml_path"] = path
        return self

    def save_json(self, path: str) -> "DtxRunnerConfigBuilder":
        """
        Sets the output file path for the results in JSON format.

        Args:
            path (str): The file path where the JSON report will be saved.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["save_json_path"] = path
        return self

    def save_html(self, path: str) -> "DtxRunnerConfigBuilder":
        """
        Sets the output file path for the results as an HTML report.

        Args:
            path (str): The file path where the HTML report will be saved.

        Returns:
            DtxRunnerConfigBuilder: The builder instance for fluent chaining.
        """
        self._data["save_html_path"] = path
        return self

    # ---------- finalization -------- #
    def build(self) -> DtxRunnerConfig:
        """
        Constructs and validates the final `DtxRunnerConfig` instance.

        This method applies any necessary defaults before creating the config
        object from the provided settings.

        Returns:
            DtxRunnerConfig: A validated configuration object ready for use.

        Raises:
            ValueError: If the final configuration is invalid due to missing
                required fields or incorrect types.
        """
        # Auto-inject defaults if missing
        self._data.setdefault("dataset", PromptDataset.HF_JAILBREAKV)
        self._data.setdefault("collector", _NullCollector())

        try:
            return DtxRunnerConfig(**self._data)
        except ValidationError as e:
            raise ValueError(f"Invalid DtxRunnerConfig: {e}") from e

# --------------------------------------------------------------------------- #
#  ReportConverter (in-file helper)                                           #
# --------------------------------------------------------------------------- #

class ReportConverter:
    """
    Lightweight helper to convert/persist EvalReport.
    Use either config-driven saving (automatic) or ad-hoc saving (manual).
    """

    # ---- HTML ----
    @staticmethod
    def to_html(report: EvalReport) -> str:
        return HTMLReportGenerator().generate(report=report)

    @staticmethod
    def save_html(report: EvalReport, path: str) -> str:
        html = ReportConverter.to_html(report)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        logger.info("HTML report saved to: {}".format(p))
        return str(p)

    # ---- JSON ----
    @staticmethod
    def to_json(report: EvalReport, indent: int = 2) -> str:
        return report.model_dump_json(indent=indent)

    @staticmethod
    def save_json(report: EvalReport, path: str, indent: int = 2) -> str:
        text = ReportConverter.to_json(report, indent=indent)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        logger.info("JSON report saved to: {}".format(p))
        return str(p)

    # ---- YAML ----
    @staticmethod
    def to_yaml(report: EvalReport) -> str:
        # Keep keys order for readability
        return yaml.safe_dump(report.model_dump(), sort_keys=False)

    @staticmethod
    def save_yaml(report: EvalReport, path: str) -> str:
        text = ReportConverter.to_yaml(report)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        logger.info("YAML report saved to: {}".format(p))
        return str(p)


# --------------------------------------------------------------------------- #
#  MAIN RUNNER                                                                #
# --------------------------------------------------------------------------- #

class DtxRunner:
    """Executes a red-team evaluation per the supplied config."""

    def __init__(self, cfg: DtxRunnerConfig) -> None:
        self.cfg = cfg
        self._report: Optional[EvalReport] = None
        self._html_report_generator = HTMLReportGenerator()

    # --------------------------- PUBLIC API -------------------------------- #

    def run(self) -> EvalReport:
        collector = self.cfg.collector or _NullCollector()     # safety net
        plan = self._load_or_generate_plan()
        self._report = self._execute_plan(plan, collector)
        self._maybe_persist()
        return self._report

    # -------------------------- INTERNALS ---------------------------------- #

    def _load_or_generate_plan(self) -> RedTeamPlan:
        if self.cfg.plan:
            return self.cfg.plan
        if self.cfg.plan_file:
            return RedTeamPlanGenerator.load_yaml(self.cfg.plan_file)

        scope_input = ScopeInput(
            description="SDK-generated scope",
            plugins=self.cfg.plugins,
            frameworks=self.cfg.frameworks, 
        )

        scope = RedTeamScopeCreator(scope_input).run()
        scope.redteam.max_prompts = self.cfg.max_prompts
        scope.redteam.max_prompts_per_plugin = self.cfg.max_prompts_per_plugin
        scope.redteam.max_goals_per_plugin = self.cfg.max_goals_per_plugin

        if self.cfg.evaluator:
            scope.redteam.global_evaluator = self.cfg.evaluator

        plan_cfg = PlanInput(dataset=self.cfg.dataset)
        return RedTeamPlanGenerator(scope=scope, config=plan_cfg).run()

    def _execute_plan(
        self,
        plan: RedTeamPlan,
        collector: BaseResultCollector,
    ) -> EvalReport:
        runner = RedTeamTestRunner()

        runner_input = RedTeamRunnerInput(
            plan=plan,
            agent=self.cfg.agent,
            collector=collector,
            override_tactics=self.cfg.tactics,
            max_prompts=self.cfg.max_prompts,
            samples_per_prompt=self.cfg.samples_per_prompt,
            threads=self.cfg.threads,
        )

        return runner.run(runner_input)


    def _maybe_persist(self) -> None:
        if not self._report:
            return
        # Use ReportConverter as single source of truth for persistence.
        if self.cfg.save_yaml_path:
            ReportConverter.save_yaml(self._report, self.cfg.save_yaml_path)

        if self.cfg.save_json_path:
            ReportConverter.save_json(self._report, self.cfg.save_json_path)

        if self.cfg.save_html_path:
            ReportConverter.save_html(self._report, self.cfg.save_html_path)
