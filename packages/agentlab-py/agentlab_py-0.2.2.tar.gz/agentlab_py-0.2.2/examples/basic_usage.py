#!/usr/bin/env python3
"""
Example usage of the AgentLab SDK in Python.

This example demonstrates how to:
- Initialize the AgentLab client with environment variable authentication
- Run evaluations with multiple evaluators
- Access and display evaluation results
- Handle errors gracefully

Setup:
1. Set your API token as an environment variable:
   export AGENTLAB_API_TOKEN=your-api-token-here
   
2. Or pass it directly to AgentLabClientOptions (api_token parameter takes precedence):
   AgentLabClientOptions(api_token='your-token-here')
"""

import asyncio
import json
import sys
import os

# Add the parent directory to the path to import agentlab
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
# Also add the project root so 'proto.agentlab' imports work
sys.path.insert(0, project_root)

from agentlab import AgentLabClient, AgentLabClientOptions, CreateEvaluationOptions


async def run_example():
    """Run a basic evaluation example."""
    
    # Initialize the client
    client = AgentLabClient(AgentLabClientOptions(
# API token is automatically loaded from AGENTLAB_API_TOKEN environment variable
    ))

    try:
        # Run evaluation with multiple evaluators (new API)
        evaluation_options = CreateEvaluationOptions(
            agent_name='test-agent',
            agent_version='1.0.0',
            evaluator_names=['correctness-v1'],
            user_question='What is the capital of France?',
            agent_answer='The capital of France is Paris.',
            ground_truth='Paris is the capital of France',
            instructions='Provide factual and accurate information',
            scores={
                'confidence': 0.95,
                'difficulty': 1,
                'verified': True
            }
        )
        
        evaluation = client.run_evaluation(evaluation_options)

        print('✅ Evaluation completed!')
        print('📊 Results:')
        
        # Access evaluator results
        evaluator_results = getattr(evaluation, 'evaluator_results', {})
        for evaluator_name, result in evaluator_results.items():
            print(f'\n🔍 {evaluator_name}:')
            print(f'  - State: {getattr(result, "state", "N/A")}')
            print(f'  - Score: {getattr(result, "score", "N/A")}')
            
            # Parse JSON output for detailed results
            try:
                output_text = getattr(result, 'output', '{}')
                output = json.loads(output_text)
                print(f'  - Rationale: {output.get("rationale", "N/A")}')
            except (json.JSONDecodeError, AttributeError):
                raw_output = getattr(result, 'output', '')
                if len(raw_output) > 100:
                    print(f'  - Raw Output: {raw_output[:100]}...')
                else:
                    print(f'  - Raw Output: {raw_output}')

        # Use helper method for structured results
        evaluation_name = getattr(evaluation, 'name', '')
        if evaluation_name:
            result_data = client.get_evaluation_result(evaluation_name)
            print('\n📈 Structured Results:')
            print(json.dumps(result_data['results'], indent=2))
        else:
            print('\n⚠️  Evaluation name not available for structured results')
            
    except Exception as error:
        print(f'❌ Error: {error}')
        return False
    
    return True


def run_sync_example():
    """Run the example synchronously."""
    
    # Initialize the client
    client = AgentLabClient(AgentLabClientOptions(
# API token is automatically loaded from AGENTLAB_API_TOKEN environment variable
    ))

    try:
        print('🚀 Starting AgentLab evaluation example...\n')
        
        # Run evaluation with multiple evaluators
        evaluation_options = CreateEvaluationOptions(
            agent_name='test-agent',
            agent_version='1.0.0',
            # project_id is now auto-filled from auth context
            evaluator_names=['correctness-v1'],
            user_question='What is the capital of France?',
            agent_answer='The capital of France is Paris.',
            ground_truth='Paris is the capital of France',
            instructions='Provide factual and accurate information',
            scores={
                'confidence': 0.95,
                'difficulty': 1,
                'verified': True
            }
        )
        
        print('📝 Running evaluation with the following parameters:')
        print(f'  - Agent: {evaluation_options.agent_name} v{evaluation_options.agent_version}')
        print(f'  - Evaluators: {", ".join(evaluation_options.evaluator_names)}')
        print(f'  - Question: {evaluation_options.user_question}')
        print(f'  - Answer: {evaluation_options.agent_answer}')
        print()
        
        evaluation = client.run_evaluation(evaluation_options)

        print('✅ Evaluation completed!')
        print('📊 Results:')
        
        # Access evaluator results
        evaluator_results = getattr(evaluation, 'evaluator_results', {})
        
        if not evaluator_results:
            print('⚠️  No evaluator results found')
            return True
            
        for evaluator_name, result in evaluator_results.items():
            print(f'\n🔍 {evaluator_name}:')
            print(f'  - State: {getattr(result, "state", "N/A")}')
            print(f'  - Score: {getattr(result, "score", "N/A")}')
            
            # Parse JSON output for detailed results
            try:
                output_text = getattr(result, 'output', '{}')
                if output_text:
                    output = json.loads(output_text)
                    print(f'  - Rationale: {output.get("rationale", "N/A")}')
                    if 'explanation' in output:
                        print(f'  - Explanation: {output["explanation"]}')
                else:
                    print('  - No output available')
            except (json.JSONDecodeError, AttributeError) as parse_error:
                raw_output = getattr(result, 'output', '')
                if len(raw_output) > 100:
                    print(f'  - Raw Output: {raw_output[:100]}...')
                else:
                    print(f'  - Raw Output: {raw_output}')
                print(f'  - Parse Error: {parse_error}')

        # Use helper method for structured results
        evaluation_name = getattr(evaluation, 'name', '')
        if evaluation_name:
            try:
                result_data = client.get_evaluation_result(evaluation_name)
                print('\n📈 Structured Results:')
                print(json.dumps(result_data['results'], indent=2))
            except Exception as e:
                print(f'\n⚠️  Could not fetch structured results: {e}')
        else:
            print('\n⚠️  Evaluation name not available for structured results')
            
    except Exception as error:
        print(f'❌ Error: {error}')
        import traceback
        print('\n🔍 Full traceback:')
        traceback.print_exc()
        return False
    
    return True


# Additional helper functions for demonstration
def list_evaluators_example():
    """Example of listing available evaluators."""
    print('\n🔍 Listing available evaluators...')
    
    client = AgentLabClient(AgentLabClientOptions(
# API token is automatically loaded from AGENTLAB_API_TOKEN environment variable
    ))
    
    try:
        response = client.list_evaluators()  # project_id auto-filled
        evaluators = getattr(response, 'evaluators', [])
        
        if evaluators:
            print(f'Found {len(evaluators)} evaluators:')
            for evaluator in evaluators:
                name = getattr(evaluator, 'name', 'Unknown')
                display_name = getattr(evaluator, 'display_name', 'No display name')
                description = getattr(evaluator, 'description', 'No description')
                print(f'  - {name}: {display_name}')
                if description:
                    print(f'    {description}')
        else:
            print('No evaluators found')
            
    except Exception as error:
        print(f'❌ Error listing evaluators: {error}')


def list_evaluation_runs_example():
    """Example of listing evaluation runs."""
    print('\n📋 Listing recent evaluation runs...')
    
    client = AgentLabClient(AgentLabClientOptions(
# API token is automatically loaded from AGENTLAB_API_TOKEN environment variable
    ))
    
    try:
        response = client.list_evaluation_runs()  # project_id auto-filled
        evaluation_runs = getattr(response, 'evaluation_runs', [])
        
        if evaluation_runs:
            print(f'Found {len(evaluation_runs)} evaluation runs:')
            for run in evaluation_runs[:5]:  # Show first 5
                name = getattr(run, 'name', 'Unknown')
                question = getattr(run, 'user_question', 'No question')
                print(f'  - {name}')
                print(f'    Question: {question[:60]}{"..." if len(question) > 60 else ""}')
        else:
            print('No evaluation runs found')
            
    except Exception as error:
        print(f'❌ Error listing evaluation runs: {error}')


# Run the example if this file is executed directly
if __name__ == '__main__':
    print('🐍 AgentLab Python Client - Basic Usage Example')
    print('=' * 50)
    
    # Run the main example
    success = run_sync_example()
    
    if success:
        print('\n' + '=' * 50)
        print('✨ Example completed successfully!')
        
        # Run additional examples
        list_evaluators_example()
        list_evaluation_runs_example()
        
        print('\n📚 Next steps:')
        print('  - Set your API token: export AGENTLAB_API_TOKEN=your-token-here')
        print('  - The project ID is now auto-detected from your auth context')
        print('  - Explore other methods like get_evaluator() and get_evaluation_run()')
        print('  - Check out the async examples for concurrent operations')
    else:
        print('\n💡 Tips for troubleshooting:')
        print('  - Set your API token: export AGENTLAB_API_TOKEN=your-token-here')
        print('  - Verify your API token is correct and has proper permissions')
        print('  - Ensure you have access to at least one project')
        print('  - Check that the evaluator names are valid')
        print('  - Verify network connectivity to the AgentLab API')
        
        sys.exit(1)
