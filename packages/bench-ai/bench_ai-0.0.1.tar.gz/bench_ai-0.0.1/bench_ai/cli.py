#!/usr/bin/env python3
"""
Bench AI CLI - Command line interface for workflow acceleration
"""

import sys
import argparse
from bench_ai import benchmark, hello, WorkflowAccelerator, DesignSpaceExplorer, __version__

def main():
    parser = argparse.ArgumentParser(
        description="🚀 Bench AI - Accelerate engineering workflows at the speed of thought",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bench-ai hello              # Get a motivational engineering message
  bench-ai benchmark          # Run the workflow acceleration benchmark
  bench-ai optimize           # Optimize a random workflow
  bench-ai explore            # Explore parallel design universes
  
Visit https://getbench.ai to supercharge your engineering team!
        """
    )
    
    parser.add_argument('--version', action='version', version=f'bench-ai {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Hello command
    hello_parser = subparsers.add_parser('hello', help='Get a greeting from the future')
    
    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Run workflow acceleration benchmark')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize a workflow')
    optimize_parser.add_argument('--workflow', type=str, default='mystery_workflow',
                                help='Name of the workflow to optimize')
    
    # Explore command
    explore_parser = subparsers.add_parser('explore', help='Explore design space')
    explore_parser.add_argument('--scenarios', type=int, default=100,
                               help='Number of parallel scenarios to explore')
    
    args = parser.parse_args()
    
    if args.command == 'hello':
        print(hello())
    elif args.command == 'benchmark':
        benchmark()
    elif args.command == 'optimize':
        accelerator = WorkflowAccelerator()
        accelerator.optimize(args.workflow)
    elif args.command == 'explore':
        explorer = DesignSpaceExplorer()
        explorer.explore(args.scenarios)
    else:
        print(hello())
        print("\nTry 'bench-ai --help' for more options!")

if __name__ == '__main__':
    main()