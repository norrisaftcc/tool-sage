"""CLI interface for SAGE learning assistant."""

import click
from sage.core.base import Flow, SharedStore
from sage.agents.orchestrator import AssistanceOrchestratorNode
from sage.agents.profile import LearningProfileNode
from sage.agents.responder import ResponseGeneratorNode


def create_sage_flow() -> Flow:
    """Create and wire up the SAGE agent flow."""
    # Initialize agents
    orchestrator = AssistanceOrchestratorNode(name="orchestrator")
    profile_agent = LearningProfileNode(name="profile")
    responder = ResponseGeneratorNode(name="respond")
    
    # Wire up the flow
    # Orchestrator decides which agent to activate
    orchestrator >> {
        "profile": profile_agent,
        "respond": responder,
        # Add more agents as we build them
        "adapt": responder,  # Placeholder
        "question": responder,  # Placeholder
        "progress": responder,  # Placeholder
        "end": None  # Termination state
    }
    
    # Profile agent returns to orchestrator for next decision
    profile_agent >> orchestrator
    
    # Responder ends the flow cycle (no return to orchestrator)
    # This prevents infinite loops
    
    # Create flow with initial shared state
    flow = Flow(
        shared=SharedStore()
    )
    
    # Initialize shared store
    flow.shared.update({
        "student_profiles": {},
        "interactions": [],
        "conversation": [],
        "current_student": "default_student",
        "learning_state": "initial"
    })
    
    flow.set_start(orchestrator)
    
    return flow


@click.group()
def cli():
    """SAGE - Scholar's Adaptive Growth Engine"""
    pass


@cli.command()
@click.option('--student', '-s', default='default_student', help='Student ID')
@click.option('--topic', '-t', default='general', help='Learning topic')
def learn(student: str, topic: str):
    """Start an interactive learning session."""
    click.echo(click.style("🎓 SAGE Learning Assistant", fg='cyan', bold=True))
    click.echo(f"Student: {student} | Topic: {topic}")
    click.echo("-" * 50)
    
    # Create the flow
    flow = create_sage_flow()
    flow.shared["current_student"] = student
    flow.shared["topic"] = topic
    
    # Initial run to get first response
    flow.run(max_steps=10)
    
    # Display initial response
    response = flow.shared.get("current_response", "Hello! I'm SAGE, your learning assistant.")
    click.echo(f"\n🤖 SAGE: {response}")
    
    # Interactive loop
    while True:
        try:
            # Get student input
            user_input = click.prompt('\n📝 You', type=str)
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                click.echo("\n👋 Thanks for learning with SAGE! See you next time.")
                break
            
            # Process input
            flow.shared["student_input"] = user_input
            
            # Add to conversation history
            flow.shared["conversation"].append({
                "role": "student",
                "content": user_input
            })
            
            # Run the flow
            flow.run(max_steps=10)
            
            # Display response
            response = flow.shared.get("current_response", "I'm processing that...")
            click.echo(f"\n🤖 SAGE: {response}")
            
            # Debug info (remove in production)
            if click.confirm('\n[Debug] Show agent activity?', default=False):
                logs = flow.shared.get("logs", [])
                for log in logs[-3:]:  # Show last 3 log entries
                    click.echo(f"  - {log}")
                    
        except KeyboardInterrupt:
            click.echo("\n\n👋 Thanks for learning with SAGE!")
            break
        except Exception as e:
            click.echo(f"\n❌ Error: {e}")
            if click.confirm('Continue?', default=True):
                continue
            else:
                break


@cli.command()
def test():
    """Run a test conversation to verify the system works."""
    click.echo("🧪 Testing SAGE system...")
    
    # Create flow
    flow = create_sage_flow()
    
    # Simulate a conversation
    test_inputs = [
        "Hello",
        "I want to learn about Python",
        "Can you test me?"
    ]
    
    for input_text in test_inputs:
        click.echo(f"\n📝 Student: {input_text}")
        flow.shared["student_input"] = input_text
        flow.run(max_steps=5)
        response = flow.shared.get("current_response", "No response")
        click.echo(f"🤖 SAGE: {response}")
    
    click.echo("\n✅ Test complete!")
    
    # Show flow history
    click.echo(f"\nFlow history: {' -> '.join(flow.history)}")


if __name__ == '__main__':
    cli()