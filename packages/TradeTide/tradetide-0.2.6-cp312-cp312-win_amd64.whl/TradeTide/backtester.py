import matplotlib.pyplot as plt
import numpy as np
from MPSPlots import helper

from TradeTide.binary.interface_backtester import BACKTESTER
from TradeTide.market import Market
from TradeTide.strategy import Strategy
import TradeTide


class Backtester(BACKTESTER):
    """
    Backtester class that extends the BACKTESTER interface for backtesting trading strategies.

    This class provides methods to run backtests, manage capital, and evaluate trading strategies
    using historical market data.

    Parameters
    ----------
    strategy : Strategy
        The trading strategy to be tested.
    exit_strategy : ExitStrategy
        The exit strategy to manage open positions.
    market : Market
        The market data on which to run the backtest.
    capital_management : CapitalManagement
        The capital management rules for the backtest.
    """

    def __init__(
        self, strategy: Strategy, exit_strategy, market: Market, capital_management
    ):
        super().__init__(
            strategy=strategy,
            exit_strategy=exit_strategy,
            market=market,
            capital_management=capital_management,
            debug_mode=TradeTide.debug_mode,
        )

        self.strategy = strategy
        self.exit_strategy = exit_strategy
        self.market = market
        self.capital_management = capital_management

    @helper.pre_plot(nrows=4, ncols=1)
    def plot(self, axes: plt.Axes) -> plt.Figure:
        """
        Create comprehensive visualization of backtesting results.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object containing all plots

        Examples
        --------
        >>> backtester.plot()  # All plots
        >>> backtester.plot('strategy', 'equity')  # Specific plots only
        >>> backtester.plot('equity', show=False)  # Don't show immediately
        """
        figure = axes[0].get_figure()

        plot_methods = [
            self._plot_strategy,
            self._plot_equity,
            self._plot_positions,
            self._plot_drawdown,
            self._plot_trades,
        ]

        for ax, plot_method in zip(axes.flatten(), plot_methods):
            plot_method(axes=ax, show=False)

        # Set common x-axis label on bottom plot
        axes[-1].set_xlabel("Time")

        # Add main title
        figure.suptitle(
            "Backtesting Results Overview", fontsize=16, fontweight="bold", y=0.98
        )

        plt.subplots_adjust(top=0.93)

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_strategy(self, axes: plt.Axes) -> None:
        """Plot market prices with strategy signals and indicators."""
        # Plot market data
        self.market.plot(axes=axes, show=False)

        # Get strategy signals
        trade_signals = self.strategy.get_trade_signal(self.market)

        # Plot buy/sell signals
        buy_signals = np.where(np.array(trade_signals) == 1)[0]
        sell_signals = np.where(np.array(trade_signals) == -1)[0]

        if len(buy_signals) > 0:
            axes.scatter(
                [self.market.dates[i] for i in buy_signals],
                [self.market.ask.close[i] for i in buy_signals],
                color="green",
                marker="^",
                s=60,
                label="Buy Signal",
                zorder=5,
            )

        if len(sell_signals) > 0:
            axes.scatter(
                [self.market.dates[i] for i in sell_signals],
                [self.market.ask.close[i] for i in sell_signals],
                color="red",
                marker="v",
                s=60,
                label="Sell Signal",
                zorder=5,
            )

        # Add indicators if available
        if hasattr(self.strategy, "indicators") and self.strategy.indicators:
            for indicator in self.strategy.indicators:
                if hasattr(indicator, "plot"):
                    indicator.plot(axes, show_metric=True)

        axes.set_ylabel("Price")
        axes.set_title("Trading Strategy Overview")
        axes.legend(loc="upper left")

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_equity(self, axes: plt.Axes) -> None:
        """Plot portfolio equity curve over time."""
        if hasattr(self, "_cpp_portfolio") and self._cpp_portfolio is not None:
            equity_data = self._cpp_portfolio.record.equity
            time_data = self._cpp_portfolio.record.time
            initial_capital = self._cpp_portfolio.record.initial_capital

            axes.plot(
                time_data,
                equity_data,
                color="blue",
                linewidth=2,
                label="Portfolio Equity",
            )
            axes.axhline(
                initial_capital,
                color="red",
                linestyle="--",
                linewidth=1,
                alpha=0.7,
                label="Initial Capital",
            )

            # Calculate and show final return
            final_return = (equity_data[-1] - initial_capital) / initial_capital * 100
            axes.text(
                0.02,
                0.98,
                f"Total Return: {final_return:.2f}%",
                transform=axes.transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )
        else:
            axes.text(
                0.5,
                0.5,
                "Portfolio data not available.\nRun backtest first.",
                transform=axes.transAxes,
                ha="center",
                va="center",
            )

        axes.set_ylabel("Equity ($)")
        axes.set_title("Portfolio Equity Curve")
        axes.legend()

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_positions(self, axes: plt.Axes) -> None:
        """Plot number of open positions over time."""
        if hasattr(self, "_cpp_portfolio") and self._cpp_portfolio is not None:
            positions_data = self._cpp_portfolio.record.concurrent_positions
            time_data = self._cpp_portfolio.record.time

            axes.step(
                time_data,
                positions_data,
                where="mid",
                color="orange",
                linewidth=2,
                label="Open Positions",
            )
            axes.fill_between(
                time_data, 0, positions_data, step="mid", color="orange", alpha=0.3
            )

            # Show max concurrent positions
            max_positions = max(positions_data) if positions_data else 0
            axes.text(
                0.02,
                0.98,
                f"Max Concurrent: {max_positions}",
                transform=axes.transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )
        else:
            axes.text(
                0.5,
                0.5,
                "Portfolio data not available.\nRun backtest first.",
                transform=axes.transAxes,
                ha="center",
                va="center",
            )

        axes.set_ylabel("# Positions")
        axes.set_title("Open Positions Over Time")
        axes.legend()

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_drawdown(self, axes: plt.Axes) -> None:
        """Plot portfolio drawdown over time."""
        if hasattr(self, "_cpp_portfolio") and self._cpp_portfolio is not None:
            equity_data = np.array(self._cpp_portfolio.record.equity)
            time_data = self._cpp_portfolio.record.time

            # Calculate running maximum (peak)
            running_max = np.maximum.accumulate(equity_data)

            # Calculate drawdown as percentage
            drawdown = (equity_data - running_max) / running_max * 100

            axes.fill_between(
                time_data, 0, drawdown, color="red", alpha=0.3, label="Drawdown"
            )
            axes.plot(time_data, drawdown, color="red", linewidth=1)

            # Show maximum drawdown
            max_drawdown = min(drawdown)
            axes.text(
                0.02,
                0.02,
                f"Max Drawdown: {max_drawdown:.2f}%",
                transform=axes.transAxes,
                verticalalignment="bottom",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )
        else:
            axes.text(
                0.5,
                0.5,
                "Portfolio data not available.\nRun backtest first.",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )

        axes.set_ylabel("Drawdown (%)")
        axes.set_title("Portfolio Drawdown")
        axes.legend()

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_trades(self, axes: plt.Axes) -> None:
        """Plot trade distribution and statistics."""
        if hasattr(self, "portfolio") and self.portfolio is not None:
            axes.text(
                0.5,
                0.5,
                "Trade analysis plot\n(Implementation depends on\navailable trade data)",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
        else:
            axes.text(
                0.5,
                0.5,
                "Portfolio data not available.\nRun backtest first.",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )

        axes.set_ylabel("Trade P&L")
        axes.set_title("Trade Distribution")

    @helper.post_mpl_plot
    def plot_summary(self) -> plt.Figure:
        """
        Create a comprehensive summary dashboard of backtesting results.

        Returns
        -------
        matplotlib.figure.Figure
            The figure object containing the summary dashboard
        """
        figure = plt.figure(figsize=(12, 8))

        # Create a 3x2 grid layout
        gs = figure.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # Strategy overview (top, full width)
        ax1 = figure.add_subplot(gs[0, :])
        self._plot_strategy(axes=ax1, show=False, tight_layout=False)

        # Equity curve (middle left)
        ax2 = figure.add_subplot(gs[1, 0])
        self._plot_equity(axes=ax2, show=False, tight_layout=False)

        # Drawdown (middle right)
        ax3 = figure.add_subplot(gs[1, 1])
        self._plot_drawdown(axes=ax3, show=False, tight_layout=False)

        # Positions (bottom left)
        ax4 = figure.add_subplot(gs[2, 0])
        self._plot_positions(axes=ax4, show=False, tight_layout=False)

        # Performance metrics (bottom right)
        ax5 = figure.add_subplot(gs[2, 1])
        self._plot_performance_metrics(axes=ax5, show=False, tight_layout=False)

        figure.suptitle(
            "Backtesting Summary Dashboard", fontsize=18, fontweight="bold", y=0.98
        )

        return figure

    @helper.pre_plot(nrows=1, ncols=1)
    def _plot_performance_metrics(self, axes: plt.Axes) -> None:
        """Display key performance metrics as text."""
        axes.axis("off")  # Hide axes for text display

        if hasattr(self, "_cpp_portfolio") and self._cpp_portfolio is not None:
            # Calculate key metrics
            equity_data = np.array(self._cpp_portfolio.record.equity)
            initial_capital = self._cpp_portfolio.record.initial_capital

            total_return = (equity_data[-1] - initial_capital) / initial_capital * 100

            # Calculate Sharpe ratio (simplified)
            returns = np.diff(equity_data) / equity_data[:-1]
            sharpe_ratio = (
                np.mean(returns) / np.std(returns) * np.sqrt(252)
                if np.std(returns) > 0
                else 0
            )

            # Calculate max drawdown
            running_max = np.maximum.accumulate(equity_data)
            drawdown = (equity_data - running_max) / running_max * 100
            max_drawdown = min(drawdown)

            # Calculate win rate (placeholder)
            win_rate = 0.0  # Would need individual trade data

            metrics_text = f"""
Performance Metrics

Total Return: {total_return:.2f}%
Sharpe Ratio: {sharpe_ratio:.2f}
Max Drawdown: {max_drawdown:.2f}%
Win Rate: {win_rate:.1f}%

Initial Capital: ${initial_capital:,.0f}
Final Equity: ${equity_data[-1]:,.0f}
"""
        else:
            metrics_text = """
Performance Metrics

No data available.
Run backtest first.
"""

        axes.text(
            0.1,
            0.9,
            metrics_text,
            transform=axes.transAxes,
            fontsize=12,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.8),
        )

        axes.set_title("Key Performance Indicators")
