# AlgoFlow Example Workflows Cookbook

A collection of practical workflow patterns and real-world examples using AlgoFlow.

## Table of Contents

1. [Data Processing Pipeline](#data-processing-pipeline)
2. [ML Training Workflow](#ml-training-workflow)
3. [ETL with Error Recovery](#etl-with-error-recovery)
4. [Parallel Web Scraping](#parallel-web-scraping)
5. [AI-Powered Analysis](#ai-powered-analysis)
6. [Event-Driven Processing](#event-driven-processing)
7. [Batch Job Orchestration](#batch-job-orchestration)

---

## Data Processing Pipeline

**Use Case:** Process CSV files through validation, cleaning, transformation, and analysis stages.

```haskell
{-# LANGUAGE OverloadedStrings #-}
import AlgoFlow
import qualified Data.ByteString.Lazy as BL
import qualified Data.Csv as Csv
import qualified Data.Vector as V

dataProcessingWorkflow :: Workflow IO
dataProcessingWorkflow = (workflow "csv-processor" steps)
    { wfConfig = config }
  where
    config = defaultConfig 
        { wcMaxWorkers = 4
        , wcCachePath = Just "/tmp/algoflow/cache"
        }
    
    steps = [validateStep, cleanStep, transformStep, analyzeStep]
    
    validateStep = step "validate" $ \inputs -> do
        csvData <- requireInput "raw_csv" inputs
        case Csv.decode Csv.NoHeader csvData of
            Left err -> throwIO $ ValidationError $ "Invalid CSV: " <> T.pack err
            Right (rows :: V.Vector (V.Vector BL.ByteString)) -> do
                let rowCount = V.length rows
                    colCount = if V.null rows then 0 else V.length (rows V.! 0)
                
                when (rowCount < 10) $ 
                    throwIO $ ValidationError "Too few rows"
                
                return $ StepResult
                    (Map.singleton "validated_csv" csvData)
                    (Map.fromList [("row_count", encode rowCount),
                                  ("col_count", encode colCount)])
    
    cleanStep = (step "clean" $ \inputs -> do
        csv <- requireInput "validated_csv" inputs
        -- Remove empty rows, trim whitespace, handle nulls
        let cleaned = cleanCsvData csv
        return $ StepResult
            (Map.singleton "clean_csv" cleaned)
            (Map.singleton "removed_rows", encode 5))
        { stepDependencies = ["validate"]
        , stepRetries = 2
        }
    
    transformStep = (step "transform" $ \inputs -> do
        csv <- requireInput "clean_csv" inputs
        -- Apply business transformations
        transformed <- applyTransformations csv
        return $ StepResult
            (Map.singleton "transformed_csv" transformed)
            Map.empty)
        { stepDependencies = ["clean"]
        , stepCache = True  -- Cache expensive transformations
        }
    
    analyzeStep = (step "analyze" $ \inputs -> do
        csv <- requireInput "transformed_csv" inputs
        -- Generate statistics
        stats <- computeStatistics csv
        report <- generateReport stats
        return $ StepResult
            (Map.fromList [("statistics", encode stats),
                          ("report", report)])
            Map.empty)
        { stepDependencies = ["transform"] }

-- Usage
main :: IO ()
main = do
    rawData <- BL.readFile "input.csv"
    result <- runWorkflow dataProcessingWorkflow 
        (Map.singleton "raw_csv" rawData)
    
    case Map.lookup "report" (wsResults result) of
        Just report -> BL.writeFile "output_report.html" report
        Nothing -> putStrLn "Workflow failed"
```

---

## ML Training Workflow

**Use Case:** Train a machine learning model with data prep, training, validation, and deployment stages.

```haskell
import AlgoFlow
import AlgoFlow.AI.Anthropic

mlTrainingWorkflow :: Workflow IO
mlTrainingWorkflow = (workflow "ml-training" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 2  -- Limit GPU usage
        , wcHooks = Map.fromList
            [("after_step_train", [logMetrics]),
             ("after_workflow", [notifyCompletion])]
        }
    
    steps = [prepData, splitData, train, validate, deploy]
    
    prepData = step "prepare-data" $ \inputs -> do
        dataset <- requireInput "dataset_path" inputs
        -- Load and preprocess data
        processed <- preprocessDataset dataset
        return $ StepResult
            (Map.singleton "processed_data" processed)
            (Map.singleton "sample_count", encode 10000)
    
    splitData = (step "split-data" $ \inputs -> do
        data <- requireInput "processed_data" inputs
        -- 80/20 train/test split
        (train, test) <- splitDataset 0.8 data
        return $ StepResult
            (Map.fromList [("train_data", train),
                          ("test_data", test)])
            Map.empty)
        { stepDependencies = ["prepare-data"] }
    
    train = (step "train" $ \inputs -> do
        trainData <- requireInput "train_data" inputs
        hyperparams <- optionalInput "hyperparameters" defaultParams inputs
        
        -- Train model (mock)
        model <- trainModel trainData hyperparams
        metrics <- evaluateModel model trainData
        
        return $ StepResult
            (Map.singleton "model" model)
            (Map.singleton "train_metrics", encode metrics))
        { stepDependencies = ["split-data"]
        , stepTimeout = Just 3600  -- 1 hour timeout
        , stepRetries = 1
        }
    
    validate = (step "validate" $ \inputs -> do
        model <- requireInput "model" inputs
        testData <- requireInput "test_data" inputs
        
        metrics <- evaluateModel model testData
        let passed = accuracy metrics > 0.85
        
        unless passed $
            throwIO $ ValidationError "Model accuracy too low"
        
        return $ StepResult
            (Map.singleton "validation_passed" (encode passed))
            (Map.singleton "test_metrics", encode metrics))
        { stepDependencies = ["train", "split-data"] }
    
    deploy = (step "deploy" $ \inputs -> do
        model <- requireInput "model" inputs
        passed <- requireInput "validation_passed" inputs
        
        when (decode passed == Just True) $ do
            endpoint <- deployModel model
            return $ StepResult
                (Map.singleton "endpoint" endpoint)
                Map.empty)
        { stepDependencies = ["validate"] }

-- Hooks
logMetrics :: Hook IO
logMetrics state = do
    putStrLn $ "Training metrics: " ++ show (wsResults state)

notifyCompletion :: Hook IO  
notifyCompletion state = do
    sendEmail "team@company.com" "Training completed" (show state)
```

---

## ETL with Error Recovery

**Use Case:** Extract data from multiple sources, transform, and load with automatic retry and error handling.

```haskell
import AlgoFlow
import Control.Exception (SomeException)

etlWorkflow :: Workflow IO
etlWorkflow = (workflow "etl-pipeline" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 6
        , wcMiddleware = [loggingMiddleware, timingMiddleware]
        }
    
    steps = extractSteps ++ [transform] ++ loadSteps
    
    -- Parallel extraction from multiple sources
    extractSteps = 
        [ (step ("extract-" <> source) $ \_ -> do
            data <- extractFromSource source
            return $ StepResult
                (Map.singleton ("raw_" <> source) data)
                Map.empty)
            { stepRetries = 3  -- Retry on network failures
            , stepTimeout = Just 30
            }
        | source <- ["postgres", "mongodb", "s3", "api"]
        ]
    
    transform = (step "transform" $ \inputs -> do
        -- Gather all extracted data
        let rawData = Map.filterWithKey (\k _ -> "raw_" `T.isPrefixOf` k) inputs
        
        -- Apply transformations
        transformed <- transformAll rawData
        validated <- validateTransformed transformed
        
        return $ StepResult
            (Map.singleton "transformed_data" validated)
            (Map.singleton "record_count", encode 50000))
        { stepDependencies = ["extract-" <> s | s <- ["postgres", "mongodb", "s3", "api"]]
        , stepCache = True
        }
    
    -- Parallel loading to destinations
    loadSteps =
        [ (step ("load-" <> dest) $ \inputs -> do
            data <- requireInput "transformed_data" inputs
            
            -- Partition data for destination
            subset <- partitionForDestination dest data
            result <- loadToDestination dest subset
            
            return $ StepResult
                Map.empty
                (Map.singleton ("loaded_" <> dest), encode result))
            { stepDependencies = ["transform"]
            , stepRetries = 5  -- Critical step, retry more
            }
        | dest <- ["warehouse", "cache", "search"]
        ]

-- Middleware
loggingMiddleware :: Middleware IO
loggingMiddleware action = do
    putStrLn "Step starting..."
    result <- action `catch` \(e :: SomeException) -> do
        putStrLn $ "Step failed: " ++ show e
        throwIO e
    putStrLn "Step completed"
    return result

timingMiddleware :: Middleware IO
timingMiddleware action = do
    start <- getCurrentTime
    result <- action
    end <- getCurrentTime
    let duration = diffUTCTime end start
    putStrLn $ "Step took: " ++ show duration
    return result
```

---

## Parallel Web Scraping

**Use Case:** Scrape multiple websites in parallel with rate limiting and result aggregation.

```haskell
import AlgoFlow
import Network.HTTP.Simple
import Control.Concurrent (threadDelay)
import Control.Concurrent.STM
import qualified Data.Text as T

webScrapingWorkflow :: Workflow IO
webScrapingWorkflow = (workflow "web-scraper" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 10  -- Parallel scraping
        }
    
    steps = [rateLimit] ++ scrapers ++ [aggregate, analyze]
    
    -- Global rate limiter setup
    rateLimit = step "setup-rate-limit" $ \_ -> do
        rateLimiter <- newTVarIO (10 :: Int)  -- 10 requests per second
        return $ StepResult
            (Map.singleton "rate_limiter" (encode rateLimiter))
            Map.empty
    
    -- Individual scraper for each URL
    scrapers = 
        [ (step ("scrape-" <> T.pack (show i)) $ \inputs -> do
            -- Rate limiting
            limiter <- requireInput "rate_limiter" inputs
            atomically $ do
                rate <- readTVar (decode limiter)
                when (rate <= 0) retry
                writeTVar (decode limiter) (rate - 1)
            
            -- Scrape
            let url = urls !! i
            response <- httpLBS =<< parseRequest url
            let content = getResponseBody response
            
            -- Parse content
            parsed <- parseHtml content
            
            return $ StepResult
                (Map.singleton ("scraped_" <> T.pack (show i)) (encode parsed))
                (Map.singleton "url" (encode url)))
            { stepDependencies = ["setup-rate-limit"]
            , stepRetries = 2
            , stepTimeout = Just 10
            }
        | (i, url) <- zip [0..] urls
        ]
    
    aggregate = (step "aggregate-results" $ \inputs -> do
        -- Collect all scraped data
        let scraped = Map.filterWithKey (\k _ -> "scraped_" `T.isPrefixOf` k) inputs
            allData = map decode $ Map.elems scraped
        
        aggregated <- combineResults allData
        
        return $ StepResult
            (Map.singleton "aggregated_data" (encode aggregated))
            (Map.singleton "total_scraped", encode (Map.size scraped)))
        { stepDependencies = ["scrape-" <> T.pack (show i) | i <- [0..length urls - 1]] }
    
    analyze = (step "analyze" $ \inputs -> do
        data <- requireInput "aggregated_data" inputs
        
        -- Analysis
        trends <- analyzeTrends (decode data)
        report <- generateScrapingReport trends
        
        return $ StepResult
            (Map.fromList [("trends", encode trends),
                          ("report", report)])
            Map.empty)
        { stepDependencies = ["aggregate-results"] }
    
    urls = [ "https://example1.com"
           , "https://example2.com"
           , "https://example3.com"
           -- ... more URLs
           ]

-- Rate limit replenisher (run in separate thread)
replenishRateLimit :: TVar Int -> IO ()
replenishRateLimit limiter = forever $ do
    threadDelay 100000  -- 100ms
    atomically $ modifyTVar limiter (\r -> min 10 (r + 1))
```

---

## AI-Powered Analysis

**Use Case:** Combine local Ollama and Anthropic API for multi-stage AI analysis.

```haskell
import AlgoFlow
import AlgoFlow.AI.Ollama
import AlgoFlow.AI.Anthropic

aiAnalysisWorkflow :: Workflow IO
aiAnalysisWorkflow = (workflow "ai-analysis" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 2  -- Limit concurrent AI calls
        , wcPersistPath = Just "/tmp/algoflow/ai-state.json"
        }
    
    steps = [quickAnalysis, deepAnalysis, synthesis, humanReview]
    
    quickAnalysis = (step "quick-analysis" $ \inputs -> do
        text <- requireInput "document" inputs
        
        -- Use local Ollama for initial analysis
        ollama <- createOllamaClient defaultOllamaConfig
        summary <- queryOllama ollama 
            "Summarize this document in 3 bullet points" 
            text
        
        topics <- queryOllama ollama
            "Extract the main topics from this document"
            text
        
        return $ StepResult
            (Map.fromList [("summary", encode summary),
                          ("topics", encode topics)])
            Map.empty)
        { stepCache = True  -- Cache to avoid re-processing
        }
    
    deepAnalysis = (step "deep-analysis" $ \inputs -> do
        doc <- requireInput "document" inputs
        summary <- requireInput "summary" inputs
        topics <- requireInput "topics" inputs
        
        -- Use Claude for deeper analysis
        client <- createAnthropicClient
        
        analysis <- queryClaude client (T.unlines
            [ "Given this document summary: " <> decode summary
            , "And these topics: " <> decode topics
            , "Provide a comprehensive analysis including:"
            , "1. Key insights and implications"
            , "2. Potential risks or concerns"
            , "3. Recommended actions"
            , "4. Areas requiring human review"
            ]) doc
        
        return $ StepResult
            (Map.singleton "deep_analysis" (encode analysis))
            Map.empty)
        { stepDependencies = ["quick-analysis"]
        , stepRetries = 3  -- Handle API failures
        , stepTimeout = Just 60
        }
    
    synthesis = (step "synthesis" $ \inputs -> do
        summary <- requireInput "summary" inputs
        analysis <- requireInput "deep_analysis" inputs
        
        -- Combine both AI outputs
        ollama <- createOllamaClient defaultOllamaConfig
        combined <- queryOllama ollama
            "Synthesize these findings into an executive brief"
            (encode $ Map.fromList [("summary", decode summary),
                                   ("analysis", decode analysis)])
        
        return $ StepResult
            (Map.singleton "synthesis" (encode combined))
            Map.empty)
        { stepDependencies = ["quick-analysis", "deep-analysis"] }
    
    humanReview = (step "human-review" $ \inputs -> do
        synthesis <- requireInput "synthesis" inputs
        analysis <- requireInput "deep_analysis" inputs
        
        -- Flag items for human review based on AI confidence
        reviewItems <- extractReviewItems (decode analysis)
        
        -- Create review dashboard
        dashboard <- createReviewDashboard synthesis reviewItems
        
        return $ StepResult
            (Map.fromList [("review_dashboard", dashboard),
                          ("review_required", encode $ not (null reviewItems))])
            Map.empty)
        { stepDependencies = ["synthesis"] }
```

---

## Event-Driven Processing

**Use Case:** Process incoming events with different handling based on event type.

```haskell
import AlgoFlow
import qualified Data.Map as Map

eventProcessingWorkflow :: Event -> Workflow IO
eventProcessingWorkflow event = (workflow "event-processor" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 1  -- Sequential for events
        }
    
    steps = [validateEvent] ++ routeSteps ++ [notify]
    
    validateEvent = step "validate" $ \_ -> do
        let valid = validateEventSchema event
        unless valid $ throwIO $ ValidationError "Invalid event schema"
        
        return $ StepResult
            (Map.singleton "event" (encode event))
            (Map.singleton "event_type" (encode $ eventType event))
    
    -- Dynamic routing based on event type
    routeSteps = case eventType event of
        "user.signup" -> [processSignup, sendWelcome]
        "order.placed" -> [validateOrder, chargePayment, fulfillOrder]
        "data.uploaded" -> [scanFile, processFile, indexFile]
        _ -> [handleUnknown]
    
    processSignup = (step "process-signup" $ \inputs -> do
        event <- requireInput "event" inputs
        -- Create user account
        userId <- createUser (decode event)
        -- Initialize preferences
        initUserPreferences userId
        
        return $ StepResult
            (Map.singleton "user_id" (encode userId))
            Map.empty)
        { stepDependencies = ["validate"] }
    
    sendWelcome = (step "send-welcome" $ \inputs -> do
        userId <- requireInput "user_id" inputs
        -- Send email
        emailId <- sendWelcomeEmail (decode userId)
        
        return $ StepResult
            Map.empty
            (Map.singleton "email_id" (encode emailId)))
        { stepDependencies = ["process-signup"] }
    
    -- ... other event handlers ...
    
    notify = (step "notify" $ \inputs -> do
        -- Send completion notification
        let eventData = Map.lookup "event" inputs
        notifyEventProcessed (decode <$> eventData)
        
        return $ StepResult Map.empty Map.empty)
        { stepDependencies = allPreviousSteps }

-- Event-driven usage
processEvent :: Event -> IO ()
processEvent event = do
    let workflow = eventProcessingWorkflow event
    result <- runWorkflow workflow Map.empty
    
    when (any isError $ Map.elems $ wsErrors result) $
        handleEventError event result
```

---

## Batch Job Orchestration

**Use Case:** Orchestrate nightly batch jobs with dependencies and monitoring.

```haskell
import AlgoFlow
import Data.Time

batchJobWorkflow :: UTCTime -> Workflow IO
batchJobWorkflow runDate = (workflow "nightly-batch" steps)
    { wfConfig = config }
  where
    config = defaultConfig
        { wcMaxWorkers = 4
        , wcHooks = Map.fromList
            [("before_workflow", [logStart]),
             ("after_workflow", [logComplete, alertOnFailure])]
        , wcPersistPath = Just $ "/var/algoflow/batch/" ++ show runDate
        }
    
    steps = [prepare] ++ dataJobs ++ [aggregate] ++ reportJobs ++ [cleanup]
    
    prepare = step "prepare-environment" $ \_ -> do
        -- Check prerequisites
        checkDiskSpace
        checkDatabaseConnections
        createWorkingDirectories runDate
        
        return $ StepResult
            (Map.singleton "run_date" (encode runDate))
            Map.empty
    
    dataJobs =
        [ (step "extract-sales" $ \inputs -> do
            date <- requireInput "run_date" inputs
            data <- extractSalesData (decode date)
            return $ StepResult
                (Map.singleton "sales_data" data)
                (Map.singleton "record_count" (encode 125000)))
            { stepDependencies = ["prepare-environment"]
            , stepRetries = 3
            }
        
        , (step "extract-inventory" $ \inputs -> do
            date <- requireInput "run_date" inputs
            data <- extractInventoryData (decode date)
            return $ StepResult
                (Map.singleton "inventory_data" data)
                Map.empty)
            { stepDependencies = ["prepare-environment"]
            , stepRetries = 3
            }
        
        , (step "process-returns" $ \inputs -> do
            date <- requireInput "run_date" inputs
            returns <- processReturns (decode date)
            return $ StepResult
                (Map.singleton "returns_data" returns)
                Map.empty)
            { stepDependencies = ["prepare-environment"] }
        ]
    
    aggregate = (step "aggregate-data" $ \inputs -> do
        sales <- requireInput "sales_data" inputs
        inventory <- requireInput "inventory_data" inputs
        returns <- requireInput "returns_data" inputs
        
        -- Complex aggregation logic
        aggregated <- performAggregation sales inventory returns
        metrics <- calculateMetrics aggregated
        
        return $ StepResult
            (Map.fromList [("aggregated", aggregated),
                          ("metrics", encode metrics)])
            Map.empty)
        { stepDependencies = ["extract-sales", "extract-inventory", "process-returns"]
        , stepCache = True
        }
    
    reportJobs =
        [ (step "generate-executive-report" $ \inputs -> do
            metrics <- requireInput "metrics" inputs
            report <- generateExecutiveReport (decode metrics)
            return $ StepResult
                (Map.singleton "exec_report" report)
                Map.empty)
            { stepDependencies = ["aggregate-data"] }
        
        , (step "generate-operational-report" $ \inputs -> do
            data <- requireInput "aggregated" inputs
            report <- generateOperationalReport data
            return $ StepResult
                (Map.singleton "ops_report" report)
                Map.empty)
            { stepDependencies = ["aggregate-data"] }
        ]
    
    cleanup = (step "cleanup" $ \inputs -> do
        -- Archive processed data
        archiveData runDate
        -- Clean temp files
        cleanTempFiles runDate
        -- Update job status
        updateJobStatus runDate "completed"
        
        return $ StepResult Map.empty Map.empty)
        { stepDependencies = ["generate-executive-report", "generate-operational-report"] }

-- Scheduling
scheduleBatchJob :: IO ()
scheduleBatchJob = do
    -- Run every night at 2 AM
    now <- getCurrentTime
    let tonight = ... -- Calculate 2 AM
    
    scheduleAt tonight $ do
        result <- runWorkflow (batchJobWorkflow tonight) Map.empty
        
        -- Check results
        case checkBatchSuccess result of
            Success -> putStrLn "Batch completed successfully"
            Failure reasons -> alertOps reasons
```

---

## Best Practices

### 1. Error Handling
- Use `stepRetries` for transient failures
- Set appropriate timeouts for external calls
- Implement circuit breakers for unreliable services
- Use specific error types for better debugging

### 2. Performance
- Enable caching for expensive computations
- Tune `wcMaxWorkers` based on workload
- Use async operations where possible
- Monitor memory usage in data-heavy workflows

### 3. Observability
- Add meaningful metadata to step results
- Use hooks for logging and monitoring
- Implement health checks in long-running steps
- Export metrics to your monitoring system

### 4. Testing
- Test steps individually before workflow integration
- Use test data generators for edge cases
- Mock external dependencies in tests
- Validate workflow DAG structure

### 5. Security
- Never put credentials in step results
- Sanitize inputs from external sources
- Use encrypted storage for sensitive data
- Implement access controls for workflow execution

These examples demonstrate AlgoFlow's flexibility in handling various real-world scenarios. Each can be adapted and extended based on specific requirements.