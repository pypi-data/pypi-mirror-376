# Pantheon Legends

A Python framework for implementing financial market analysis "legends" (methodologies), converted from C# contracts to idiomatic Python using dataclasses and type hints.

## Overview

Pantheon Legends provides a framework for implementing and orchestrating multiple financial analysis methodologies such as Dow Theory, Wyckoff Method, Elliott Wave, etc. The framework includes example implementations to demonstrate the structure, but **does not include actual legend implementations**.

## Features

- **Async/Await Support**: All analysis operations are asynchronous for better performance
- **Type Safety**: Full type hints using Python's typing system
- **Progress Reporting**: Real-time progress updates during analysis
- **Quality Metadata**: Comprehensive data quality metrics for each analysis
- **Extensible Design**: Easy to add new legend engines
- **Orchestration**: Run multiple legend engines concurrently
- **Example Implementations**: Demo engines showing the framework structure

## Installation

```bash
# Install from PyPI
pip install pantheon-legends

# Test installation
python -c "import legends; legends.test_installation()"

# Or install from source
git clone https://github.com/SpartanDigitalDotNet/pantheon-legends
cd pantheon-legends
pip install -e .
```

## Important Note

**This package provides a framework for implementing financial analysis legend engines, not the legend implementations themselves.**

The included `DowLegendEngine` and `WyckoffLegendEngine` are **demonstration engines only** that generate sample data to show the framework structure. They do not perform actual Dow Theory or Wyckoff Method analysis.

To use this framework for real analysis, you need to:

1. **Implement actual legend logic** in your custom engines
2. **Connect to real market data sources** 
3. **Apply the specific methodology algorithms** (Dow Theory, Wyckoff, etc.)
4. **Replace the demo data** with real analysis results

## Converting Your Scanner to a Legend

If you have an existing market scanner, you can easily convert it to a Pantheon Legend:

```bash
# Interactive scanner conversion tool
python -m legends create
```

This will guide you through:
- **Scanner characteristics** (signals, timeframes, data needs)
- **Generate a template** with your scanner structure
- **Provide clear TODO markers** where to integrate your code
- **Include test functions** to verify your legend works

Example workflow:
```
📊 What's the name of your scanner? ResonanceBreakout
🔍 What signals does it detect? breakout, volume_spike, momentum  
📈 What timeframes does it work with? 1m, 5m
📊 What data does it need? price, volume, moving_averages

🎉 Success! Created resonancebreakoutlegend.py
```

## Quick Start

### Basic Usage

```python
import asyncio
from datetime import datetime
from legends import Pantheon, LegendRequest

async def main():
    # Create Pantheon with default engines
    pantheon = Pantheon.create_default()
    
    # Create an analysis request
    request = LegendRequest(
        symbol="AAPL",
        timeframe="1d", 
        as_of=datetime.now()
    )
    
    # Unified analysis with automatic consensus
    result = await pantheon.analyze_with_consensus(request)
    
    # Individual engine results
    for engine_result in result.engine_results:
        print(f"{engine_result.legend}: {engine_result.facts}")
    
    # Automatic consensus (no manual orchestration required)
    if result.consensus:
        print(f"\nConsensus: {result.consensus.signal.value}")
        print(f"Confidence: {result.consensus.confidence:.1%}")
        print(f"Quality: {result.consensus.consensus_quality}")

asyncio.run(main())
```

## 🎯 Unified Consensus Analysis

The framework provides **automatic consensus calculation** with no manual orchestration required:

### Key Features
- **Automatic Consensus**: Consensus calculated automatically from real engine results
- **Reliability Weighting**: Engines weighted by reliability and confidence
- **One-Call Analysis**: Single method call for engines + consensus
- **Flexible Filtering**: Filter by reliability, engine type, or specific engines

### Quick Analysis
```python
# All-in-one analysis (no setup required)
from legends import quick_analysis, consensus_only

# Complete analysis with consensus
result = await quick_analysis("SPY", timeframe="1D")
print(f"Consensus: {result.consensus.signal.value}")

# Consensus-only analysis
consensus = await consensus_only("BTCUSD", min_reliability=ReliabilityLevel.HIGH)
print(f"Signal: {consensus.signal.value} ({consensus.confidence:.1%})")
```

### Advanced Consensus Options
```python
# Filtered by reliability
result = await pantheon.analyze_with_consensus(
    request,
    min_consensus_reliability=ReliabilityLevel.HIGH
)

# Specific engines only
result = await pantheon.analyze_with_consensus(
    request,
    engine_names=["Dow Theory", "Wyckoff Method"]
)

# Traditional engines consensus
traditional_result = await pantheon.analyze_with_consensus(
    request,
    engine_names=["Dow Theory", "Wyckoff Method"],
    enable_consensus=True
)
```

### Using Individual Engines

```python
import asyncio
from datetime import datetime
from legends import DowLegendEngine, LegendRequest

async def main():
    # Create a demo legend engine (not actual Dow Theory implementation)
    dow_engine = DowLegendEngine()
    
    request = LegendRequest(
        symbol="MSFT",
        timeframe="4h",
        as_of=datetime.now()
    )
    
    # Run the demo analysis
    result = await dow_engine.run_async(request)
    
    print(f"Demo Result: {result.facts['primary_trend']}")
    print(f"Confidence: {result.facts['confidence_score']}")

asyncio.run(main())
```

### Progress Monitoring

```python
import asyncio
from legends import LegendProgress

async def progress_handler(progress: LegendProgress):
    print(f"[{progress.legend}] {progress.stage}: {progress.percent:.1f}%")

# Use with any engine
result = await engine.run_async(request, progress_handler)
```

## Core Components

### Data Models

- **`LegendRequest`**: Analysis request with symbol, timeframe, and timestamp
- **`LegendProgress`**: Progress updates during analysis execution  
- **`LegendEnvelope`**: Complete analysis results with metadata
- **`QualityMeta`**: Data quality metrics (sample size, freshness, completeness)

### Engines

- **`DowLegendEngine`**: Demo implementation showing Dow Theory structure
- **`WyckoffLegendEngine`**: Demo implementation showing Wyckoff Method structure
- **Custom Engines**: Implement `ILegendEngine` protocol for real analysis

### Orchestration

- **`Pantheon`**: Manages multiple engines and provides unified interface
- **Progress Callbacks**: Real-time progress reporting
- **Concurrent Execution**: Run multiple engines simultaneously

## Creating Custom Legend Engines

```python
from legends.contracts import ILegendEngine, LegendRequest, LegendEnvelope

class MyCustomLegend:
    @property
    def name(self) -> str:
        return "MyLegend"
    
    async def run_async(self, request: LegendRequest, progress_callback=None):
        # Your analysis logic here
        facts = {"signal": "bullish", "strength": 0.85}
        quality = QualityMeta(100.0, 30.0, 1.0)
        
        return LegendEnvelope(
            legend=self.name,
            at=request.as_of, 
            tf=request.timeframe,
            facts=facts,
            quality=quality
        )

# Register with Pantheon
pantheon = Pantheon()
pantheon.register_engine(MyCustomLegend())
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/SpartanDigitalDotNet/pantheon-legends
cd pantheon-legends

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black legends/
isort legends/
```

### Type Checking

```bash
mypy legends/
```

## API Reference

### LegendRequest

```python
@dataclass(frozen=True)
class LegendRequest:
    symbol: str          # Financial instrument symbol
    timeframe: str       # Time interval (e.g., "1d", "4h", "1m")
    as_of: datetime      # Analysis timestamp
```

### LegendEnvelope

```python
@dataclass(frozen=True) 
class LegendEnvelope:
    legend: str                    # Engine name
    at: datetime                   # Analysis time
    tf: str                        # Timeframe
    facts: Dict[str, Any]          # Analysis results
    quality: QualityMeta           # Quality metrics
```

### ILegendEngine Protocol

```python
class ILegendEngine(Protocol):
    @property
    def name(self) -> str: ...
    
    async def run_async(
        self,
        request: LegendRequest,
        progress_callback: Optional[ProgressCallback] = None
    ) -> LegendEnvelope: ...
```

## Examples

See `examples.py` for comprehensive usage examples including:

- Single engine execution
- Multi-engine orchestration  
- Custom engine implementation
- Progress monitoring
- Error handling

## License

MIT License - see LICENSE file for details.

## Contributing Your Legend

Have a working legend? Share it with the community!

### **Quick Start:**
1. **Convert your scanner**: `python -m legends create`
2. **Implement your logic** in the generated template
3. **Test thoroughly** with real market data
4. **Submit a pull request** to share with others

### **Community Guidelines:**
- **Clear documentation** of what your legend detects
- **Example usage** with sample outputs
- **Performance characteristics** (speed, accuracy, etc.)
- **Data requirements** and dependencies

### **Legend Naming:**
- Use descriptive names: `BreakoutDetector`, `VolumeSpike`, `MomentumShift`
- Include version if iterating: `BreakoutDetectorV2`
- Mention methodology: `WyckoffAccumulation`, `DowTrendConfirmation`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Roadmap

- [ ] Additional built-in legend engines
- [ ] Data source integrations
- [ ] Performance optimizations
- [ ] Advanced orchestration features
- [ ] Web API interface
- [ ] Real-time streaming support
