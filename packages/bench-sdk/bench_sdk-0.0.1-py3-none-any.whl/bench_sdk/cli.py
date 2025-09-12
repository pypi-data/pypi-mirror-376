#!/usr/bin/env python3
"""
Bench SDK CLI - Command line interface for the Bench AI SDK
"""

import sys
import argparse
from bench_sdk import quickstart, demo_api, BenchSDK, AgentConfig, CADOptimizer, __version__

def main():
    parser = argparse.ArgumentParser(
        description="🛠️  Bench SDK - Build AI-powered engineering automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bench-sdk quickstart        # Run the quickstart demo
  bench-sdk api-demo          # Demonstrate API functionality
  bench-sdk optimize          # Optimize a CAD model
  bench-sdk agent             # Create and run an AI agent
  
Visit https://getbench.ai to build real engineering automation!
        """
    )
    
    parser.add_argument('--version', action='version', version=f'bench-sdk {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Quickstart command
    quickstart_parser = subparsers.add_parser('quickstart', help='Run the SDK quickstart demo')
    
    # API demo command
    api_parser = subparsers.add_parser('api-demo', help='Demonstrate API functionality')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize a CAD model')
    optimize_parser.add_argument('--model', type=str, default='demo_part',
                                help='Name of the model to optimize')
    
    # Agent command
    agent_parser = subparsers.add_parser('agent', help='Create and run an AI agent')
    agent_parser.add_argument('--name', type=str, default='DemoAgent',
                             help='Name of the agent')
    agent_parser.add_argument('--task', type=str, default='Optimize design parameters',
                             help='Task for the agent to execute')
    
    # SDK info command
    info_parser = subparsers.add_parser('info', help='Show SDK information')
    
    args = parser.parse_args()
    
    if args.command == 'quickstart':
        quickstart()
    elif args.command == 'api-demo':
        demo_api()
    elif args.command == 'optimize':
        CADOptimizer.optimize(args.model)
    elif args.command == 'agent':
        sdk = BenchSDK()
        sdk.connect()
        config = AgentConfig(
            name=args.name,
            capabilities=["CAD automation", "Simulation", "Optimization"]
        )
        agent = sdk.create_agent(config)
        result = agent.execute(args.task)
        print(f"\n📋 Result: {result}")
    elif args.command == 'info':
        print(f"\n🛠️  Bench SDK v{__version__}")
        print("=" * 50)
        print("The SDK for building AI-powered engineering automation")
        print("\nCapabilities:")
        print("  • Create AI agents for engineering tasks")
        print("  • Define and run automated workflows")
        print("  • Optimize CAD models with AI")
        print("  • Integrate with existing engineering tools")
        print("\n🌐 Learn more at https://getbench.ai")
    else:
        print("🚀 Welcome to Bench SDK!")
        print("Try 'bench-sdk --help' for available commands")
        print("Or visit https://getbench.ai to get started!")

if __name__ == '__main__':
    main()