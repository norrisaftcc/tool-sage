# SAGE Adaptive Learning Framework

## Framework Vision

SAGE is a framework for building adaptive learning systems based on the principle that **learning is a graph traversal problem**. Rather than a single application, SAGE provides composable components for creating personalized learning experiences.

### Key Insight
- **Learning paths** are directed graphs
- **Agents** are pedagogical strategies  
- **Nodes** are learning activities
- **Edges** are adaptive transitions

See [VISION.md](VISION.md) for detailed framework philosophy.

---

# Original Design: SAGE Adaptive Learning Assistant System

Looking at PocketFlow's elegant minimalist design, I'll help you plan an adaptive learning assistant system that leverages its core philosophy. Let me first examine the PocketFlow repository to understand any additional context beyond the comprehensive documentation you've provided.Now let me explore the Multi-Agent cookbook to understand PocketFlow's approach to agent coordination:Let me search for more information about PocketFlow's multi-agent capabilities:Now I have a comprehensive understanding of PocketFlow. Let me design an adaptive learning assistant system based on this minimalist framework. I'll create a system that leverages multiple specialized agents working together to provide personalized learning experiences.

## Adaptive Learning Assistant System - Design Document

### System Overview

The Adaptive Learning Assistant System is an "agent swarm" built on PocketFlow's minimalist architecture. It consists of specialized agents that collaborate to provide personalized, adaptive learning experiences. The system leverages PocketFlow's core concepts (Node, Shared Store, Flow) to create a dynamic learning environment that adapts to individual student needs.

### Core Design Principles

1. **Minimalist Architecture**: Following PocketFlow's philosophy, each agent is simple and focused
2. **Composable Components**: Agents can be combined and reconfigured for different learning scenarios
3. **Shared Knowledge Base**: All agents communicate through a central shared store
4. **Adaptive Behavior**: The system learns from student interactions and adjusts accordingly

### Agent Architecture

#### 1. **Learning Profile Agent**
- **Purpose**: Tracks and analyzes student learning patterns
- **Node Structure**:
  - `prep`: Retrieves student interaction history
  - `exec`: Analyzes learning patterns using LLM
  - `post`: Updates student profile with insights

```python
class LearningProfileNode(Node):
    def prep(self, shared):
        return {
            "student_id": shared.get("current_student"),
            "interaction_history": shared.get("interactions", []),
            "current_topic": shared.get("topic")
        }
    
    def exec(self, data):
        profile_prompt = f"""
        Analyze the student's learning patterns:
        History: {data['interaction_history']}
        Current Topic: {data['current_topic']}
        
        Return YAML with:
        - learning_style: visual/auditory/kinesthetic
        - pace: slow/medium/fast
        - comprehension_level: beginner/intermediate/advanced
        - strengths: []
        - areas_for_improvement: []
        """
        return call_llm(profile_prompt)
    
    def post(self, shared, prep_res, exec_res):
        profile = yaml.safe_load(exec_res)
        shared["student_profiles"][prep_res["student_id"]] = profile
        return "analyze_complete"
```

#### 2. **Content Adaptation Agent**
- **Purpose**: Modifies learning content based on student profile
- **Node Structure**:
  - `prep`: Gathers student profile and base content
  - `exec`: Adapts content to match learning style
  - `post`: Stores adapted content

```python
class ContentAdaptationNode(Node):
    def prep(self, shared):
        student_id = shared["current_student"]
        return {
            "profile": shared["student_profiles"].get(student_id),
            "base_content": shared["lesson_content"],
            "topic": shared["topic"]
        }
    
    def exec(self, data):
        adapt_prompt = f"""
        Adapt this content for the student:
        Profile: {data['profile']}
        Content: {data['base_content']}
        
        Create {data['profile']['learning_style']} focused content
        at {data['profile']['pace']} pace
        for {data['profile']['comprehension_level']} level
        """
        return call_llm(adapt_prompt)
    
    def post(self, shared, prep_res, exec_res):
        shared["adapted_content"] = exec_res
        return "content_ready"
```

#### 3. **Question Generation Agent**
- **Purpose**: Creates personalized assessment questions
- **Uses**: `AsyncParallelBatchNode` for generating multiple questions simultaneously

```python
class QuestionGenerationNode(AsyncParallelBatchNode):
    def prep_async(self, shared):
        profile = shared["student_profiles"][shared["current_student"]]
        # Generate different question types based on profile
        question_types = ["conceptual", "application", "analysis"]
        return [(qtype, profile, shared["topic"]) for qtype in question_types]
    
    async def exec_async(self, data):
        qtype, profile, topic = data
        prompt = f"""
        Generate a {qtype} question about {topic}
        for {profile['comprehension_level']} level student
        Output in YAML:
        - question: 
        - options: []
        - correct_answer:
        - explanation:
        """
        return await call_llm_async(prompt)
    
    def post_async(self, shared, prep_res, exec_results):
        questions = [yaml.safe_load(result) for result in exec_results]
        shared["assessment_questions"] = questions
        return "questions_generated"
```

#### 4. **Progress Tracking Agent**
- **Purpose**: Monitors learning progress and triggers interventions
- **Decision Node**: Uses branching to determine next action

```python
class ProgressMonitorNode(Node):
    def prep(self, shared):
        return {
            "student_id": shared["current_student"],
            "recent_scores": shared.get("assessment_scores", []),
            "time_on_topic": shared.get("topic_time", 0)
        }
    
    def exec(self, data):
        # Analyze progress and decide action
        avg_score = sum(data["recent_scores"]) / len(data["recent_scores"]) if data["recent_scores"] else 0
        
        decision_prompt = f"""
        Student progress analysis:
        Average Score: {avg_score}
        Time on Topic: {data['time_on_topic']} minutes
        
        Decide next action (return only the action):
        - continue: Student is progressing well
        - review: Student needs reinforcement
        - advance: Student has mastered the topic
        - assist: Student needs help
        """
        return call_llm(decision_prompt).strip()
    
    def post(self, shared, prep_res, exec_res):
        shared["progress_decision"] = exec_res
        return exec_res  # This becomes the action for branching
```

#### 5. **Assistance Orchestrator Agent** (Central Coordinator)
- **Purpose**: Coordinates all other agents
- **Flow Management**: Implements the main learning loop

```python
class AssistanceOrchestratorNode(Node):
    def prep(self, shared):
        return {
            "student_request": shared.get("student_input"),
            "current_state": shared.get("learning_state", "initial"),
            "available_agents": ["profile", "adapt", "question", "progress"]
        }
    
    def exec(self, data):
        orchestrate_prompt = f"""
        Current state: {data['current_state']}
        Student request: {data['student_request']}
        
        Determine next agent to activate:
        - profile: Update student profile
        - adapt: Adapt content
        - question: Generate questions
        - progress: Check progress
        - respond: Direct response to student
        
        Return YAML:
        - next_agent:
        - reason:
        """
        result = yaml.safe_load(call_llm(orchestrate_prompt))
        return result["next_agent"]
    
    def post(self, shared, prep_res, exec_res):
        shared["next_agent"] = exec_res
        return exec_res
```

### Flow Design

```python
def create_adaptive_learning_flow():
    # Initialize nodes
    orchestrator = AssistanceOrchestratorNode()
    profile_analyzer = LearningProfileNode()
    content_adapter = ContentAdaptationNode()
    question_generator = QuestionGenerationNode()
    progress_monitor = ProgressMonitorNode()
    
    # Student interaction nodes
    student_input = StudentInputNode()
    response_generator = ResponseGeneratorNode()
    
    # Create main flow with branching
    orchestrator >> {
        "profile": profile_analyzer,
        "adapt": content_adapter,
        "question": question_generator,
        "progress": progress_monitor,
        "respond": response_generator
    }
    
    # Each specialized agent returns to orchestrator
    profile_analyzer >> orchestrator
    content_adapter >> response_generator >> orchestrator
    question_generator >> response_generator >> orchestrator
    
    # Progress monitor can branch to different interventions
    progress_monitor >> {
        "continue": orchestrator,
        "review": content_adapter,
        "advance": topic_advancement_node,
        "assist": human_tutor_alert_node
    }
    
    # Create the flow
    flow = Flow(
        shared={
            "student_profiles": {},
            "interactions": [],
            "assessment_scores": [],
            "learning_paths": {},
            "content_library": {}
        }
    )
    
    return flow
```

### Multi-Agent Communication Pattern

Using PocketFlow's shared store pattern with message queues for agent coordination:

```python
class AgentMessageQueue:
    def __init__(self, shared):
        shared["message_queues"] = {
            "profile_updates": [],
            "content_requests": [],
            "assessment_results": [],
            "intervention_alerts": []
        }
    
    @staticmethod
    def send_message(shared, queue_name, message):
        shared["message_queues"][queue_name].append({
            "timestamp": time.time(),
            "message": message
        })
    
    @staticmethod
    def get_messages(shared, queue_name):
        messages = shared["message_queues"][queue_name]
        shared["message_queues"][queue_name] = []  # Clear after reading
        return messages
```

### Key Features

1. **Adaptive Content Delivery**
   - Content automatically adjusts based on learning style
   - Pace modifications based on comprehension speed
   - Multiple representation formats (visual, textual, interactive)

2. **Intelligent Assessment**
   - Questions generated at appropriate difficulty levels
   - Parallel generation for efficiency
   - Immediate feedback with explanations

3. **Progress Monitoring**
   - Real-time tracking of student performance
   - Automatic intervention triggers
   - Learning path optimization

4. **Scalability**
   - Async parallel processing for multiple students
   - Lightweight agent design (following PocketFlow's 100-line philosophy)
   - Easy addition of new specialized agents

### Implementation Benefits

1. **Simplicity**: Each agent is focused and simple to understand
2. **Flexibility**: Agents can be easily added, removed, or modified
3. **Transparency**: All state is visible in the shared store
4. **Reliability**: Built-in retry logic and fallback mechanisms
5. **Performance**: Async parallel execution for scalability

### Future Extensions

1. **Peer Learning Agent**: Connects students with similar learning patterns
2. **Resource Recommendation Agent**: Suggests external learning materials
3. **Parent/Teacher Dashboard Agent**: Provides progress reports
4. **Gamification Agent**: Adds achievement and motivation elements

This design leverages PocketFlow's minimalist philosophy while creating a sophisticated adaptive learning system through the composition of simple, focused agents.