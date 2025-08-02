# AlgoFlow - Setup and Installation Guide

AlgoFlow is a functional workflow engine for composable algorithmic pipelines written in Haskell.

## Prerequisites

### System Requirements
- Linux (Ubuntu 20.04+ or similar)
- 4GB RAM minimum (8GB recommended)
- GHC 9.2+ and Cabal 3.6+ OR Stack 2.9+

### Optional AI Integration
- Ollama for local LLM execution
- Anthropic API key for Claude integration

## Quick Start

### 1. Install Haskell Toolchain

**Option A: GHCup (Recommended)**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh
source ~/.bashrc
ghcup install ghc 9.2.8
ghcup install cabal 3.10.1.0
ghcup set ghc 9.2.8
```

**Option B: Stack**
```bash
curl -sSL https://get.haskellstack.org/ | sh
```

### 2. Clone and Build AlgoFlow

```bash
git clone https://github.com/yourusername/algoflow.git
cd algoflow

# Using Cabal
cabal update
cabal build

# OR using Stack
stack build
```

### 3. Install Ollama (Optional)

For local LLM-powered steps:

```bash
curl -fsSL https://ollama.ai/install.sh | sh
systemctl status ollama  # Verify it's running

# Pull a model (e.g., Mistral)
ollama pull mistral
```

### 4. Configure AI Providers (Optional)

Create `~/.algoflow/config.yaml`:

```yaml
# Local Ollama configuration
ollama:
  endpoint: "http://localhost:11434"
  model: "mistral"
  timeout: 30

# Anthropic API configuration  
anthropic:
  api_key: ${ANTHROPIC_API_KEY}  # Set via environment variable
  model: "claude-3-opus-20240229"
  max_tokens: 4096
```

Set environment variables:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Basic Usage Example

### Simple Workflow

```haskell
import AlgoFlow
import qualified Data.Map as Map
import Data.Aeson (encode)

main :: IO ()
main = do
    -- Define steps
    let step1 = step "fetch-data" $ \_ -> do
            -- Fetch some data
            return $ StepResult 
                (Map.singleton "data" (encode [1,2,3,4,5]))
                Map.empty
    
    let step2 = (step "process" $ \inputs -> do
            nums <- requireInput "data" inputs
            -- Process the data
            return $ StepResult
                (Map.singleton "result" (encode (sum <$> decode nums)))
                Map.empty)
            { stepDependencies = ["fetch-data"] }
    
    -- Create and run workflow
    let wf = workflow "example" [step1, step2]
    result <- runWorkflow wf Map.empty
    
    print result
```

### AI-Enhanced Workflow

```haskell
import AlgoFlow
import AlgoFlow.AI.Ollama    -- Provided separately
import AlgoFlow.AI.Anthropic -- Provided separately

main :: IO ()
main = do
    -- Initialize AI clients
    ollamaClient <- createOllamaClient defaultOllamaConfig
    anthropicClient <- createAnthropicClient
    
    -- Step using local Ollama
    let analyzeLocal = step "local-analysis" $ \inputs -> do
            text <- requireInput "text" inputs
            response <- queryOllama ollamaClient "Analyze this text for sentiment" text
            return $ StepResult 
                (Map.singleton "sentiment" (encode response))
                Map.empty
    
    -- Step using Anthropic API
    let deepAnalysis = (step "deep-analysis" $ \inputs -> do
            sentiment <- requireInput "sentiment" inputs
            response <- queryClaude anthropicClient 
                "Provide detailed insights based on this sentiment analysis" 
                sentiment
            return $ StepResult
                (Map.singleton "insights" (encode response))
                Map.empty)
            { stepDependencies = ["local-analysis"]
            , stepRetries = 3  -- Retry on API failures
            }
    
    -- Run workflow
    let wf = workflow "ai-pipeline" [analyzeLocal, deepAnalysis]
    result <- runWorkflow wf (Map.singleton "text" "Your text here...")
```

## Project Structure

```
algoflow/
├── src/
│   ├── AlgoFlow.hs           # Core workflow engine
│   ├── AlgoFlow/
│   │   ├── AI/
│   │   │   ├── Ollama.hs     # Ollama integration
│   │   │   └── Anthropic.hs  # Anthropic integration
│   │   ├── Cache.hs          # Caching implementation
│   │   └── Telemetry.hs      # OpenTelemetry support
├── examples/
│   ├── simple.hs             # Basic examples
│   └── ai-workflow.hs        # AI integration examples
├── test/
├── algoflow.cabal
└── stack.yaml
```

## Running Tests

```bash
# Using Cabal
cabal test

# Using Stack  
stack test

# With coverage
cabal test --enable-coverage
```

## Development Setup

### Setting up LSP (Language Server)

```bash
# Install HLS
ghcup install hls

# For VS Code, install "Haskell" extension
# For Neovim, configure with your LSP client
```

### Running in Development

```bash
# Auto-reload on changes
ghcid --command "cabal repl" --test ":main"

# With Stack
stack build --file-watch
```

## Troubleshooting

### Common Issues

1. **Ollama connection refused**
   ```bash
   # Check if Ollama is running
   systemctl status ollama
   sudo systemctl start ollama
   ```

2. **Anthropic API rate limits**
   - Configure retries in your steps
   - Use exponential backoff (built-in with `stepRetries`)

3. **Out of memory during compilation**
   ```bash
   # Limit parallel builds
   cabal build -j1
   # OR
   stack build -j1
   ```

4. **Dependency conflicts**
   ```bash
   # Clean and rebuild
   cabal clean
   rm -rf dist-newstyle
   cabal build
   ```

## Performance Tuning

### Parallelism Configuration

```haskell
let config = defaultConfig 
    { wcMaxWorkers = 8  -- Increase parallel steps
    , wcCachePath = Just "/tmp/algoflow-cache"
    }

let wf = (workflow "name" steps) { wfConfig = config }
```

### Memory Settings

For large workflows:
```bash
# Increase RTS heap size
./my-workflow +RTS -H1G -A128M -RTS
```

## Security Considerations

- Never commit API keys to version control
- Use environment variables or secure secret management
- Consider running Ollama in a container for isolation
- Review the privacy policy for telemetry data collection

## Getting Help

- GitHub Issues: https://github.com/yourusername/algoflow/issues
- Documentation: https://algoflow.readthedocs.io
- Community Discord: https://discord.gg/algoflow

## License

MIT+xyzzy License - See LICENSE file for details