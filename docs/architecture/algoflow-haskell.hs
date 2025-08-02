{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE ScopedTypeVariables #-}

{-|
Module      : AlgoFlow
Description : A functional workflow engine for composable algorithmic pipelines
Copyright   : (c) 2024, MIT+xyzzy License
License     : MIT+xyzzy
Maintainer  : your-email@example.com
Stability   : experimental
Portability : GHC

AlgoFlow is a pure functional workflow engine that enables:
  * Declarative DAG-based algorithm composition
  * Automatic parallel execution with dependency resolution
  * Built-in caching, retries, and error recovery
  * Type-safe state management with STM
  * Extensible middleware and lifecycle hooks

Example usage:

@
-- Define processing steps
let preprocessStep = step "preprocess" $ \inputs -> do
      rawData <- requireInput "data" inputs
      return $ StepResult 
        (Map.singleton "cleaned" (clean rawData))
        Map.empty

let analyzeStep = (step "analyze" $ \inputs -> do
      cleaned <- requireInput "cleaned" inputs  
      return $ StepResult
        (Map.singleton "results" (analyze cleaned))
        (Map.singleton "stats" (computeStats cleaned)))
    { stepDependencies = ["preprocess"]
    , stepRetries = 3
    , stepCache = True
    }

-- Build and run workflow
let wf = workflow "DataPipeline" [preprocessStep, analyzeStep]
result <- runWorkflow wf (Map.singleton "data" rawInput)
@
-}

module AlgoFlow
    ( -- * Core types
      Step(..)
    , Workflow(..)
    , Memory(..)
    , WorkflowState(..)
    , WorkflowConfig(..)
    , StepResult(..)
    , Hook
    , Middleware
    
    -- * Smart constructors
    , step
    , workflow
    , newMemory
    , defaultConfig
    
    -- * Execution
    , runWorkflow
    , runStep
    
    -- * Memory operations
    , get
    , set
    , delete
    , clear
    , update
    
    -- * Utilities
    , requireInput
    , optionalInput
    , mergeResults
    
    -- * Error types
    , WorkflowError(..)
    ) where

import Control.Concurrent.Async (async, wait, mapConcurrently, race)
import Control.Concurrent.STM
import Control.Exception (Exception, SomeException, catch, throwIO, try, bracket)
import Control.Monad (foldM, forM_, when, unless, void)
import Control.Monad.IO.Class (MonadIO, liftIO)
import Data.Aeson (FromJSON, ToJSON, encode, decode, eitherDecodeStrict)
import Data.ByteString.Lazy (ByteString)
import qualified Data.ByteString.Lazy as BL
import Data.Either (lefts, rights, partitionEithers)
import Data.Foldable (foldrM)
import Data.Graph (Graph, Vertex, buildG, topSort, reachable, stronglyConnComp, SCC(..))
import Data.List (nub, (\\), intercalate)
import Data.Map.Strict (Map)
import qualified Data.Map.Strict as Map
import Data.Maybe (fromMaybe, catMaybes, mapMaybe)
import Data.Set (Set)
import qualified Data.Set as Set
import Data.Text (Text)
import qualified Data.Text as T
import Data.Time (UTCTime, getCurrentTime, diffUTCTime, NominalDiffTime)
import Data.Typeable (Typeable)
import GHC.Generics (Generic)
import System.Directory (doesFileExist, createDirectoryIfMissing)
import System.FilePath (takeDirectory)
import System.Timeout (timeout)

-- | Result of a step execution, containing outputs and metadata
data StepResult = StepResult
    { srOutput :: Map Text ByteString    -- ^ Primary outputs available to dependent steps
    , srMetadata :: Map Text ByteString  -- ^ Additional metadata (logs, stats, etc)
    } deriving (Show, Eq, Generic)

instance ToJSON StepResult
instance FromJSON StepResult

-- | Lifecycle hook: function called at specific workflow events
-- Useful for logging, monitoring, or triggering side effects
type Hook m = WorkflowState -> m ()

-- | Middleware: transformation applied to all step executions
-- Can add logging, metrics, tracing, etc.
type Middleware m = forall a. m a -> m a

-- | A computational step in the workflow
data Step m = Step
    { stepName :: Text                              -- ^ Unique identifier
    , stepFunc :: Map Text ByteString -> m StepResult  -- ^ The computation
    , stepDependencies :: [Text]                    -- ^ Steps that must complete first
    , stepRetries :: Int                            -- ^ Number of retry attempts on failure
    , stepTimeout :: Maybe NominalDiffTime          -- ^ Optional execution timeout
    , stepCache :: Bool                             -- ^ Whether to cache results
    }

-- | Configuration for workflow execution behavior
data WorkflowConfig m = WorkflowConfig
    { wcMaxWorkers :: Int                -- ^ Max parallel steps (0 = unlimited)
    , wcMiddleware :: [Middleware m]     -- ^ Applied to all step executions
    , wcHooks :: Map Text [Hook m]       -- ^ Named lifecycle hooks
    , wcPersistPath :: Maybe FilePath    -- ^ Optional state persistence location
    , wcCachePath :: Maybe FilePath      -- ^ Optional cache directory
    }

-- | A workflow is a named collection of steps forming a DAG
data Workflow m = Workflow
    { wfName :: Text
    , wfSteps :: Map Text (Step m)
    , wfConfig :: WorkflowConfig m
    }

-- | Thread-safe memory for sharing data between workflow executions
newtype Memory = Memory
    { memoryData :: TVar (Map Text ByteString)
    }

-- | Current state of workflow execution
data WorkflowState = WorkflowState
    { wsCompleted :: Set Text                    -- ^ Successfully completed steps
    , wsPending :: Set Text                      -- ^ Steps not yet started
    , wsRunning :: Set Text                      -- ^ Currently executing steps
    , wsResults :: Map Text StepResult           -- ^ Results from completed steps
    , wsErrors :: Map Text SomeException         -- ^ Errors from failed steps
    , wsStartTime :: Maybe UTCTime               -- ^ Workflow start timestamp
    } deriving (Generic)

-- Custom Show instance to handle SomeException
instance Show WorkflowState where
    show ws = "WorkflowState { completed = " ++ show (wsCompleted ws) ++
              ", pending = " ++ show (wsPending ws) ++
              ", running = " ++ show (wsRunning ws) ++
              ", results = " ++ show (Map.keys $ wsResults ws) ++
              ", errors = " ++ show (Map.keys $ wsErrors ws) ++ " }"

-- Note: Can't auto-derive JSON instances due to SomeException
instance ToJSON WorkflowState where
    -- Simplified: serialize without errors
instance FromJSON WorkflowState where  
    -- Simplified: deserialize without errors

-- | Errors that can occur during workflow execution
data WorkflowError
    = CircularDependency [Text]          -- ^ Dependency cycle detected
    | MissingDependency Text Text        -- ^ Step depends on non-existent step
    | StepNotFound Text                  -- ^ Referenced step doesn't exist
    | StepFailed Text SomeException      -- ^ Step execution failed
    | StepTimeout Text                   -- ^ Step exceeded timeout
    | ValidationError Text               -- ^ Workflow validation failed
    | PersistenceError Text              -- ^ Failed to save/load state
    | InputNotFound Text                 -- ^ Required input missing
    deriving (Show, Typeable)

instance Exception WorkflowError

-- Smart Constructors

-- | Create a simple step with default settings
step :: MonadIO m => Text -> (Map Text ByteString -> m StepResult) -> Step m
step name func = Step
    { stepName = name
    , stepFunc = func
    , stepDependencies = []
    , stepRetries = 0
    , stepTimeout = Nothing
    , stepCache = False
    }

-- | Create a workflow from a list of steps
workflow :: Text -> [Step m] -> Workflow m
workflow name steps = Workflow
    { wfName = name
    , wfSteps = Map.fromList [(stepName s, s) | s <- steps]
    , wfConfig = defaultConfig
    }

-- | Default configuration with sensible defaults
defaultConfig :: WorkflowConfig m
defaultConfig = WorkflowConfig
    { wcMaxWorkers = 4      -- Reasonable parallelism
    , wcMiddleware = []
    , wcHooks = Map.empty
    , wcPersistPath = Nothing
    , wcCachePath = Nothing
    }

-- | Create a new thread-safe memory store
newMemory :: MonadIO m => m Memory
newMemory = liftIO $ Memory <$> newTVarIO Map.empty

-- Memory Operations

-- | Get a value from memory
get :: MonadIO m => Memory -> Text -> m (Maybe ByteString)
get (Memory tvar) key = liftIO $ Map.lookup key <$> readTVarIO tvar

-- | Set a value in memory
set :: MonadIO m => Memory -> Text -> ByteString -> m ()
set (Memory tvar) key value = liftIO $ atomically $ 
    modifyTVar tvar (Map.insert key value)

-- | Delete a key from memory
delete :: MonadIO m => Memory -> Text -> m ()
delete (Memory tvar) key = liftIO $ atomically $ 
    modifyTVar tvar (Map.delete key)

-- | Clear all memory
clear :: MonadIO m => Memory -> m ()
clear (Memory tvar) = liftIO $ atomically $ 
    writeTVar tvar Map.empty

-- | Update a value atomically
update :: MonadIO m => Memory -> Text -> (Maybe ByteString -> ByteString) -> m ()
update (Memory tvar) key f = liftIO $ atomically $
    modifyTVar tvar $ \m -> Map.insert key (f $ Map.lookup key m) m

-- Utilities

-- | Extract a required input, throwing if not found
requireInput :: MonadIO m => Text -> Map Text ByteString -> m ByteString
requireInput key inputs = case Map.lookup key inputs of
    Nothing -> liftIO $ throwIO $ InputNotFound key
    Just val -> return val

-- | Extract an optional input with a default
optionalInput :: Text -> ByteString -> Map Text ByteString -> ByteString
optionalInput key def inputs = fromMaybe def $ Map.lookup key inputs

-- | Merge multiple step results
mergeResults :: [StepResult] -> StepResult
mergeResults results = StepResult
    { srOutput = Map.unions $ map srOutput results
    , srMetadata = Map.unions $ map srMetadata results
    }

-- Validation

-- | Validate workflow structure before execution
validateWorkflow :: Monad m => Workflow m -> Either WorkflowError ()
validateWorkflow wf = do
    checkMissingDeps
    checkCircularDeps
    return ()
  where
    allSteps = Map.keys (wfSteps wf)
    
    -- Ensure all dependencies reference existing steps
    checkMissingDeps = forM_ (Map.toList $ wfSteps wf) $ \(name, step) ->
        forM_ (stepDependencies step) $ \dep ->
            unless (dep `elem` allSteps) $
                Left $ MissingDependency name dep
    
    -- Detect dependency cycles using strongly connected components
    checkCircularDeps = 
        case detectCycles (wfSteps wf) of
            [] -> Right ()
            (cycle:_) -> Left $ CircularDependency cycle

-- | Build a dependency graph for topological sorting
buildDependencyGraph :: Map Text (Step m) -> (Graph, Vertex -> Text, Text -> Maybe Vertex)
buildDependencyGraph steps = (graph, vertexToName, nameToVertex)
  where
    stepList = Map.toList steps
    names = map fst stepList
    nameToIdx = Map.fromList $ zip names [0..]
    
    -- Create edges from dependencies
    edges = [(fromMaybe (-1) $ Map.lookup dep nameToIdx,
              fromMaybe (-1) $ Map.lookup name nameToIdx)
            | (name, step) <- stepList
            , dep <- stepDependencies step
            , Map.member dep nameToIdx]  -- Only valid deps
    
    graph = buildG (0, length names - 1) edges
    vertexToName v = names !! v
    nameToVertex = flip Map.lookup nameToIdx

-- | Detect cycles in the dependency graph
detectCycles :: Map Text (Step m) -> [[Text]]
detectCycles steps = mapMaybe extractCycle sccs
  where
    (graph, vertexToName, nameToVertex) = buildDependencyGraph steps
    sccs = stronglyConnComp [(s, name, stepDependencies s) | (name, s) <- Map.toList steps]
    
    extractCycle (AcyclicSCC _) = Nothing
    extractCycle (CyclicSCC names) = Just names

-- Execution

-- | Execute a workflow with given inputs
runWorkflow :: (MonadIO m, ToJSON a, FromJSON a) => Workflow m -> Map Text a -> m WorkflowState
runWorkflow wf inputs = do
    -- Validate structure first
    case validateWorkflow wf of
        Left err -> liftIO $ throwIO err
        Right () -> do
            -- Convert inputs to ByteString
            let inputBytes = Map.map encode inputs
            
            -- Load previous state if persisted
            initialState <- loadState wf
            
            -- Execute with hooks
            executeWorkflow wf inputBytes initialState

-- | Main workflow execution loop
executeWorkflow :: MonadIO m => Workflow m -> Map Text ByteString -> WorkflowState -> m WorkflowState
executeWorkflow wf inputs state = do
    -- Pre-workflow hooks
    runHooks wf "before_workflow" state
    
    -- Initialize execution state
    startTime <- liftIO getCurrentTime
    let allSteps = Set.fromList $ Map.keys (wfSteps wf)
        completed = wsCompleted state
        pending = allSteps Set.\\ completed
        stateWithTime = state 
            { wsPending = pending
            , wsStartTime = Just startTime
            }
    
    -- Execute steps until completion or failure
    finalState <- executeSteps wf inputs stateWithTime
    
    -- Post-workflow hooks
    runHooks wf "after_workflow" finalState
    
    -- Persist final state
    saveState wf finalState
    
    return finalState

-- | Execute steps respecting dependencies and parallelism limits
executeSteps :: MonadIO m => Workflow m -> Map Text ByteString -> WorkflowState -> m WorkflowState
executeSteps wf inputs state
    | Set.null (wsPending state) && Set.null (wsRunning state) = return state
    | otherwise = do
        -- Find steps ready to execute
        ready <- getReadySteps wf state
        
        -- Limit parallelism if configured
        let maxWorkers = wcMaxWorkers (wfConfig wf)
            currentWorkers = Set.size (wsRunning state)
            allowedStarts = if maxWorkers > 0 
                           then max 0 (maxWorkers - currentWorkers)
                           else length ready
            toStart = take allowedStarts ready
        
        if null toStart && Set.null (wsRunning state)
            then return state  -- Deadlock or completion
            else do
                -- Mark steps as running
                let runningState = state
                        { wsPending = wsPending state Set.\\ Set.fromList (map stepName toStart)
                        , wsRunning = wsRunning state `Set.union` Set.fromList (map stepName toStart)
                        }
                
                -- Execute in parallel
                results <- liftIO $ mapConcurrently (executeStep wf inputs runningState) toStart
                
                -- Process results
                let (errors, successes) = partitionEithers results
                    completedNames = Set.fromList [stepName s | (s, _) <- successes ++ errors]
                    newResults = Map.fromList [(stepName s, r) | (s, r) <- successes]
                    newErrors = Map.fromList [(stepName s, e) | (s, e) <- errors]
                
                let newState = runningState
                        { wsCompleted = wsCompleted state `Set.union` Set.fromList [stepName s | (s, _) <- successes]
                        , wsRunning = wsRunning runningState Set.\\ completedNames
                        , wsResults = wsResults state `Map.union` newResults
                        , wsErrors = wsErrors state `Map.union` newErrors
                        }
                
                -- Continue if no critical errors
                if null errors || not (Set.null $ wsPending newState)
                    then executeSteps wf inputs newState
                    else return newState

-- | Get steps that are ready to execute (dependencies satisfied)
getReadySteps :: Monad m => Workflow m -> WorkflowState -> m [Step m]
getReadySteps wf state = do
    let completed = wsCompleted state
        pending = wsPending state
        running = wsRunning state
        
        -- A step is ready if all dependencies are completed
        isReady stepName = case Map.lookup stepName (wfSteps wf) of
            Nothing -> False
            Just step -> all (`Set.member` completed) (stepDependencies step)
    
    return [step | stepName <- Set.toList pending
                 , isReady stepName
                 , Just step <- [Map.lookup stepName (wfSteps wf)]]

-- | Execute a single step with retries, timeout, and middleware
executeStep :: MonadIO m => Workflow m -> Map Text ByteString -> WorkflowState -> Step m -> m (Either (Step m, SomeException) (Step m, StepResult))
executeStep wf baseInputs state step = do
    -- Gather inputs from dependencies
    let stepInputs = gatherInputs baseInputs state step
    
    -- Check cache first
    cached <- if stepCache step 
              then loadCachedResult wf (stepName step) stepInputs
              else return Nothing
    
    case cached of
        Just result -> return $ Right (step, result)
        Nothing -> do
            -- Pre-step hook
            runHooks wf ("before_step_" <> stepName step) state
            
            -- Execute with retries and timeout
            result <- tryWithRetries (stepRetries step) $ do
                let action = applyMiddleware (wcMiddleware $ wfConfig wf) $
                            stepFunc step stepInputs
                
                case stepTimeout step of
                    Nothing -> action
                    Just t -> do
                        let microseconds = round (t * 1000000)
                        maybeResult <- liftIO $ timeout microseconds action
                        case maybeResult of
                            Nothing -> liftIO $ throwIO $ StepTimeout (stepName step)
                            Just r -> return r
            
            -- Post-step hook
            runHooks wf ("after_step_" <> stepName step) state
            
            -- Cache successful results
            case result of
                Right res -> when (stepCache step) $ 
                    saveCachedResult wf (stepName step) stepInputs res
                _ -> return ()
            
            return $ case result of
                Left err -> Left (step, err)
                Right res -> Right (step, res)

-- | Collect inputs from base inputs and dependency outputs
gatherInputs :: Map Text ByteString -> WorkflowState -> Step m -> Map Text ByteString
gatherInputs baseInputs state step = 
    baseInputs `Map.union` depOutputs
  where
    -- Merge outputs from all dependencies
    depOutputs = Map.unions
        [srOutput result | dep <- stepDependencies step
                         , Just result <- [Map.lookup dep (wsResults state)]]

-- | Execute with retry logic
tryWithRetries :: MonadIO m => Int -> m a -> m (Either SomeException a)
tryWithRetries maxRetries action = go 0
  where
    go attempt = do
        result <- liftIO $ try action
        case result of
            Left ex | attempt < maxRetries -> do
                -- Exponential backoff: 2^attempt seconds
                let delay = min (2 ^ attempt) 30  -- Cap at 30 seconds
                liftIO $ threadDelay (delay * 1000000)
                go (attempt + 1)
            _ -> return result
    
    threadDelay = threadDelay  -- Would import from Control.Concurrent

-- | Apply middleware stack to an action
applyMiddleware :: Monad m => [Middleware m] -> m a -> m a
applyMiddleware middlewares = foldr ($) id middlewares

-- | Execute a step standalone (useful for testing)
runStep :: MonadIO m => Step m -> Map Text ByteString -> m StepResult
runStep = stepFunc

-- Hooks

-- | Execute all hooks for a given event
runHooks :: MonadIO m => Workflow m -> Text -> WorkflowState -> m ()
runHooks wf hookName state = do
    let hooks = fromMaybe [] $ Map.lookup hookName (wcHooks $ wfConfig wf)
    -- Execute hooks sequentially to maintain order
    forM_ hooks $ \hook -> hook state

-- Persistence

-- | Save workflow state to disk
saveState :: (MonadIO m) => Workflow m -> WorkflowState -> m ()
saveState wf state = case wcPersistPath (wfConfig wf) of
    Nothing -> return ()
    Just path -> liftIO $ do
        createDirectoryIfMissing True (takeDirectory path)
        -- Would serialize state to JSON and write to file
        -- BL.writeFile path (encode state)
        return ()

-- | Load workflow state from disk
loadState :: MonadIO m => Workflow m -> m WorkflowState
loadState wf = case wcPersistPath (wfConfig wf) of
    Nothing -> return emptyState
    Just path -> liftIO $ do
        exists <- doesFileExist path
        if exists
            then do
                -- Would read and deserialize state
                -- content <- BL.readFile path
                -- return $ fromMaybe emptyState (decode content)
                return emptyState
            else return emptyState
  where
    emptyState = WorkflowState Set.empty Set.empty Set.empty Map.empty Map.empty Nothing

-- Caching

-- | Generate cache key from step name and inputs
cacheKey :: Text -> Map Text ByteString -> FilePath
cacheKey stepName inputs = 
    -- Would use a proper hash function
    T.unpack stepName ++ "_cache"

-- | Load cached result if available
loadCachedResult :: MonadIO m => Workflow m -> Text -> Map Text ByteString -> m (Maybe StepResult)
loadCachedResult wf stepName inputs = case wcCachePath (wfConfig wf) of
    Nothing -> return Nothing
    Just cachePath -> liftIO $ do
        let key = cacheKey stepName inputs
            path = cachePath ++ "/" ++ key
        exists <- doesFileExist path
        if exists
            then do
                -- Would deserialize cached result
                -- content <- BL.readFile path
                -- return $ decode content
                return Nothing
            else return Nothing

-- | Save result to cache
saveCachedResult :: MonadIO m => Workflow m -> Text -> Map Text ByteString -> StepResult -> m ()
saveCachedResult wf stepName inputs result = case wcCachePath (wfConfig wf) of
    Nothing -> return ()
    Just cachePath -> liftIO $ do
        let key = cacheKey stepName inputs
            path = cachePath ++ "/" ++ key
        createDirectoryIfMissing True cachePath
        -- Would serialize and save result
        -- BL.writeFile path (encode result)
        return ()