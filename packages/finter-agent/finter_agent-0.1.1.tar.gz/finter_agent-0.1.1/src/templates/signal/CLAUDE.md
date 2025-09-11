# CLAUDE.md

This file provides orchestration guidance for the Finter quantitative signal research workspace.

## Project Overview

Finter quantitative signal research workspace for developing and backtesting trading strategies using a multi-agent architecture.

## Agent Architecture and Roles

### Super Agent (Main Claude)
- **User Interaction**: Primary interface for understanding user requirements and strategy objectives
- **Strategy Direction**: Guide users in articulating their trading hypotheses and research goals
- **Final Evaluation**: Assess completed strategies for absolute positive returns and model quality
- **Delegation**: Route alpha generation and review tasks to specialized sub-agents

### Sub-Agents
- **finter-alpha-generator** (`.claude/agents/finter-alpha-generator.md`): Develops quantitative trading strategies based on user requirements
- **finter-alpha-reviewer** (`.claude/agents/finter-alpha-reviewer.md`): Reviews strategies for methodological errors, bias, and performance issues

## Development Standards

- **Package Management**: All agents use `uv run` for Python execution
- **Project Structure**: Strategies organized in `research/strategy_name/` folders

## Strategy Development Workflow

When developing a new Alpha strategy:

1. **Requirements Gathering**: Super agent discusses strategy objectives and hypotheses with user
2. **Strategy Generation**: Delegate to finter-alpha-generator agent for implementation
   - Create `research/strategy_name/` folder structure
   - Implement strategy using `uv run` for all Python operations
3. **Strategy Review**: Delegate to finter-alpha-reviewer agent for validation and backtesting
   - Use `signal.backtest()` method for backtesting (NOT external backtest scripts)
   - Use `uv run` for executing tests and strategy validation
   - Validate using proper scoped imports from strategy folder
4. **Final Assessment**: Super agent evaluates if strategy achieves:
   - Absolute positive returns (not just relative outperformance)
   - Strong risk-adjusted performance metrics
   - Robust methodology without critical flaws
   - Practical implementability

## Key Development Guidelines

**Critical Areas Requiring Extra Attention**:
- **Position Sizing**: Most time-consuming aspect - avoid ranking normalization, use portfolio allocation
- **Look-ahead Bias**: Use windowed data for calculations, avoid future information
- **Data Handling**: Proper NaN/inf handling and vectorization for performance
- **Testing**: Edge case validation and bias prevention checks
- **Backtesting**: Always use `signal.backtest()` method, not external backtest scripts