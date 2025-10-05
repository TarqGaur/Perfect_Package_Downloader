#!/usr/bin/env python3
"""
AI-Powered Python Package Conflict Resolver v2.0
Enhanced with intelligent web search and continuous learning
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
import glob

# Import from your existing modules
try:
    from LLM import addhistory, init_history
    from runthis import safe_json_parse
    HAS_AI = True
except ImportError as e:
    print(f"Warning: Could not import AI modules: {e}")
    print("Running in non-AI mode...")
    HAS_AI = False


class EnhancedAIConflictResolver:
    def __init__(self, json_path: str, max_ai_iterations: int = 8):
        self.json_path = Path(json_path)
        self.data = None
        self.execution_log = []
        self.max_ai_iterations = max_ai_iterations
        self.ai_consultation_count = 0
        self.web_search_count = 0
        self.history_name = "conflict_resolver_v2"
        self.solved = False
        self.solution_history = []  # Track all attempted solutions
        
        # Initialize AI history if available
        if HAS_AI:
            init_history(self.history_name)
    
    def find_latest_analysis_files(self) -> List[Path]:
        """Find all analysis attempt files"""
        pattern1 = "exectest1_attempt*.json"
        pattern2 = "exectest2_attempt*.json"
        
        files1 = sorted(Path(".").glob(pattern1), key=lambda x: x.stat().st_mtime, reverse=True)
        files2 = sorted(Path(".").glob(pattern2), key=lambda x: x.stat().st_mtime, reverse=True)
        
        return files1 + files2
    
    def load_json(self) -> bool:
        """Load and validate the JSON file"""
        try:
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            
            # Handle nested structure
            if 'data' in self.data and 'llm' in self.data['data']:
                self.data = self.data['data']['llm']
            
            print(f"✅ Loaded {self.json_path}")
            return True
        except FileNotFoundError:
            print(f"❌ Error: File '{self.json_path}' not found")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON: {e}")
            return False
    
    def load_all_analysis_attempts(self) -> List[Dict]:
        """Load all analysis attempts to learn from them"""
        all_files = self.find_latest_analysis_files()
        analyses = []
        
        print(f"\n📚 Loading {len(all_files)} previous analysis files...")
        
        for file_path in all_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    analyses.append({
                        'file': str(file_path),
                        'data': data,
                        'timestamp': file_path.stat().st_mtime
                    })
                    print(f"   ✅ {file_path.name}")
            except Exception as e:
                print(f"   ⚠️ Could not load {file_path}: {e}")
        
        return analyses
    
    def display_summary(self):
        """Display analysis summary"""
        print("\n" + "="*70)
        print("📊 CONFLICT ANALYSIS SUMMARY")
        print("="*70)
        print(f"Status: {self.data.get('overall_status', 'Unknown').upper()}")
        print(f"Summary: {self.data.get('summary', 'N/A')}")
        
        # Web search info
        if self.data.get('web_search_performed'):
            print(f"\n🌐 Web Search: Performed")
            if 'web_search_findings' in self.data:
                print(f"Findings: {self.data['web_search_findings'][:100]}...")
        
        issues = self.data.get('issues_found', [])
        if issues:
            print(f"\n⚠️ Issues Found: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                print(f"  [{i}] {issue.get('description', 'N/A')}")
                print(f"      Severity: {issue.get('severity', 'unknown').upper()}")
                if issue.get('web_verified'):
                    print(f"      ✓ Web Verified")
        print("="*70)
    
    def execute_command(self, command: str, description: str = "") -> Tuple[bool, str]:
        """Execute a command and return success status"""
        print(f"\n🔧 Executing: {command}")
        if description:
            print(f"   Purpose: {description}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            # Check for errors in output even if return code is 0
            has_error = any(err in output.lower() for err in ['error:', 'failed', 'could not', 'conflict'])
            actual_success = success and not has_error
            
            status = "✅ SUCCESS" if actual_success else f"❌ FAILED (code: {result.returncode})"
            print(f"   Result: {status}")
            
            if not actual_success and output.strip():
                print(f"   Output: {output[:300]}...")
            
            self.execution_log.append({
                'command': command,
                'success': actual_success,
                'output': output,
                'exit_code': result.returncode,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'description': description
            })
            
            return actual_success, output
            
        except subprocess.TimeoutExpired:
            print("   Result: ⏱️ TIMEOUT")
            return False, "Command timeout"
        except Exception as e:
            print(f"   Result: ❌ ERROR - {e}")
            return False, str(e)
    
    def trigger_web_search_consultation(self, failed_solutions: List[Dict], original_issue: str) -> Optional[Dict]:
        """Trigger AI to perform web searches for current solutions"""
        if not HAS_AI:
            print("❌ AI consultation unavailable")
            return None
        
        if self.ai_consultation_count >= self.max_ai_iterations:
            print(f"⚠️ Max AI consultations reached ({self.max_ai_iterations})")
            return None
        
        self.ai_consultation_count += 1
        self.web_search_count += 1
        
        print(f"\n{'='*70}")
        print(f"🌐 AI WEB SEARCH CONSULTATION #{self.web_search_count}")
        print(f"{'='*70}")
        
        # Extract error messages for targeted searching
        error_messages = []
        for solution in failed_solutions:
            if 'output' in solution:
                output = solution['output']
                # Extract actual error lines
                for line in output.split('\n'):
                    if any(err in line.lower() for err in ['error', 'conflict', 'requires', 'incompatible']):
                        error_messages.append(line.strip())
        
        # Build comprehensive web search prompt
        ai_prompt = f"""You are an expert Python package resolver with web search capabilities.

CRITICAL SITUATION - ALL AUTOMATED SOLUTIONS HAVE FAILED
Consultation #{self.ai_consultation_count}

ORIGINAL PROBLEM:
{original_issue}

FAILED SOLUTIONS ({len(failed_solutions)}):
{json.dumps(failed_solutions[:3], indent=2)}

EXTRACTED ERROR MESSAGES:
{chr(10).join(error_messages[:5])}

SOLUTION HISTORY (what we've already tried):
{json.dumps(self.solution_history[-10:], indent=2)}

🔍 MANDATORY WEB SEARCH TASKS:

1. **Search for exact error messages**
   - Use the exact error text as search query
   - Look for StackOverflow solutions from 2024-2025
   - Find GitHub issues with similar problems

2. **Search version compatibility**
   - "[package1] [package2] version compatibility 2025"
   - "[package1] [package2] working together"
   - Check official compatibility matrices

3. **Search official documentation**
   - Find official installation guides
   - Check known issues and workarounds
   - Look for migration guides if versions changed

4. **Search community solutions**
   - Reddit threads about similar conflicts
   - Blog posts with working solutions
   - Package maintainer recommendations

5. **Alternative approaches**
   - Search for alternative packages
   - Look for compatibility layers
   - Find wrapper libraries that handle conflicts

RESPONSE FORMAT (ONLY JSON):
{{
  "web_searches_performed": [
    {{
      "query": "exact search query used",
      "findings": "key insights discovered",
      "source_urls": ["url1", "url2"],
      "relevance": "high/medium/low",
      "solution_type": "version_change/alternative_package/workaround"
    }}
  ],
  "root_cause_analysis": "Deep dive into why ALL previous solutions failed",
  "new_strategy": "Completely different approach based on web research",
  "confidence_level": "high/medium/low based on web verification",
  "recommended_solutions": [
    {{
      "solution_type": "commands",
      "priority": 1,
      "description": "What this does (based on web research)",
      "source": "URL or reference to where this solution was found",
      "web_verified": true,
      "different_because": "How this is different from failed attempts",
      "undo_commands": [],
      "commands": ["exact pip commands"],
      "verification_command": "pip check && python -c 'import package'",
      "expected_outcome": "What should happen",
      "fallback_if_fails": "What to try next if this fails"
    }}
  ],
  "alternative_packages": [
    {{
      "original": "problematic-package",
      "alternative": "alternative-package",
      "reason": "Why this alternative is better",
      "compatibility": "Known to work with other packages"
    }}
  ],
  "should_continue": true/false,
  "next_steps": "What to do if this consultation also fails"
}}

CRITICAL REQUIREMENTS:
- You MUST actually perform web searches (you have this capability)
- DO NOT suggest anything we've already tried in solution_history
- Provide at least 3 completely different solutions
- Each solution must be web-verified with source URLs
- Include confidence levels based on web research quality
- Suggest alternative packages if original ones are problematic
- ONLY return valid JSON, no other text"""

        try:
            print("🔍 Initiating AI web search...")
            print("   Searching for current solutions and compatibility info...")
            
            # Use enhanced access for web search
            response = addhistory(
                user_msg=ai_prompt,
                use_enhanced_access=True,
                history_name=self.history_name,
                save_to_file=f"web_search_consultation_{self.web_search_count}.json"
            )
            
            if not response:
                print("❌ No AI response received")
                return None
            
            # Extract AI response
            last_key = sorted(response.keys(), key=int)[-1]
            ai_data = response[last_key]['llm']
            
            # Check if AI used web search
            if ai_data.get('used_search'):
                print("✅ AI successfully performed web searches")
                if 'search_queries' in ai_data:
                    print(f"   Queries: {', '.join(ai_data['search_queries'][:3])}")
            else:
                print("⚠️ AI may not have performed web searches")
            
            # Parse main_response
            main_response = ai_data.get('main_response', '')
            if isinstance(main_response, str):
                try:
                    parsed = safe_json_parse(main_response)
                    if 'recommended_solutions' in parsed:
                        num_solutions = len(parsed['recommended_solutions'])
                        print(f"✅ AI provided {num_solutions} web-verified solutions")
                        
                        if 'web_searches_performed' in parsed:
                            print(f"   Web searches: {len(parsed['web_searches_performed'])} queries")
                        
                        if 'confidence_level' in parsed:
                            print(f"   Confidence: {parsed['confidence_level']}")
                        
                        return parsed
                except:
                    pass
            
            # Fallback
            if isinstance(ai_data, dict) and 'recommended_solutions' in ai_data:
                return ai_data
            
            print("❌ Could not extract solutions from AI response")
            return None
            
        except Exception as e:
            print(f"❌ AI consultation error: {e}")
            return None
    
    def apply_solution(self, solution: Dict, solution_num: int) -> Tuple[bool, List[Dict]]:
        """Apply a solution automatically"""
        print(f"\n{'='*70}")
        print(f"🔧 APPLYING SOLUTION #{solution_num}")
        print(f"{'='*70}")
        print(f"Description: {solution.get('description', 'N/A')}")
        print(f"Priority: {solution.get('priority', 'N/A')}")
        
        if solution.get('web_verified'):
            print("✓ Web Verified Solution")
        if solution.get('source'):
            print(f"Source: {solution['source']}")
        
        failed_commands = []
        
        # Track this solution
        self.solution_history.append({
            'solution_num': solution_num,
            'description': solution.get('description', ''),
            'commands': solution.get('commands', []),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Execute undo commands
        undo_commands = solution.get('undo_commands', [])
        if undo_commands:
            print("\n↩️ Executing undo commands...")
            for cmd in undo_commands:
                self.execute_command(cmd, "Undo previous changes")
                time.sleep(1)
        
        # Execute main commands
        solution_type = solution.get('solution_type', '')
        
        if solution_type == 'commands':
            commands = solution.get('commands', [])
            if not commands:
                print("⚠️ No commands to execute")
                return False, []
            
            print("\n🚀 Executing solution commands...")
            all_success = True
            
            for cmd in commands:
                success, output = self.execute_command(cmd)
                
                if not success:
                    all_success = False
                    failed_commands.append({
                        'command': cmd,
                        'output': output,
                        'exit_code': 1
                    })
                
                time.sleep(1)
            
            # Run verification command if provided
            if all_success and solution.get('verification_command'):
                print("\n✓ Running verification command...")
                success, _ = self.execute_command(
                    solution['verification_command'],
                    "Verify solution"
                )
                if success:
                    print("✅ Verification passed!")
                    self.solved = True
                else:
                    print("⚠️ Verification failed")
                    all_success = False
            
            return all_success, failed_commands
        
        else:
            print(f"⏭️ Skipping non-command solution type: {solution_type}")
            return False, []
    
    def continuous_resolution_loop(self) -> bool:
        """Enhanced resolution loop that continues until solved or max iterations"""
        if not self.load_json():
            return False
        
        self.display_summary()
        
        if self.data.get('overall_status') == 'success':
            print("\n✅ No conflicts detected - all packages installed successfully")
            return True
        
        # Load all previous analysis attempts for context
        all_analyses = self.load_all_analysis_attempts()
        print(f"\n📖 Loaded {len(all_analyses)} previous analysis attempts for learning")
        
        solutions = self.data.get('recommended_solutions', [])
        if not solutions:
            print("\n⚠️ No solutions available in JSON")
            return False
        
        # Filter to command-based solutions
        solutions = [s for s in solutions if s.get('solution_type') == 'commands']
        solutions.sort(key=lambda x: x.get('priority', 999))
        
        print(f"\n🎯 Starting continuous resolution")
        print(f"   Initial solutions: {len(solutions)}")
        print(f"   Max AI iterations: {self.max_ai_iterations}")
        print(f"{'='*70}")
        
        original_issue = self.data.get('summary', 'Package conflict')
        iteration = 0
        max_total_iterations = 20
        consecutive_failures = 0
        
        while iteration < max_total_iterations and not self.solved:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"🔄 RESOLUTION ITERATION {iteration}/{max_total_iterations}")
            print(f"{'='*70}")
            print(f"AI Consultations: {self.ai_consultation_count}/{self.max_ai_iterations}")
            print(f"Web Searches: {self.web_search_count}")
            print(f"Solutions in Queue: {len(solutions)}")
            
            if not solutions:
                print("\n⚠️ No more solutions to try")
                break
            
            success_count = 0
            all_failed_commands = []
            
            # Try each solution
            for i, solution in enumerate(solutions, 1):
                success, failed_cmds = self.apply_solution(solution, i)
                
                if success:
                    success_count += 1
                    consecutive_failures = 0
                    print(f"\n✅ Solution #{i}: SUCCESS")
                    
                    # Final verification
                    print("\n🔍 Running final verification...")
                    verify_cmd = "pip check"
                    verify_success, _ = self.execute_command(verify_cmd, "Final dependency check")
                    
                    if verify_success:
                        print("\n🎉 {'='*70}")
                        print("🎉 RESOLUTION SUCCESSFUL!")
                        print(f"🎉 {'='*70}")
                        print(f"   Total iterations: {iteration}")
                        print(f"   AI consultations: {self.ai_consultation_count}")
                        print(f"   Web searches: {self.web_search_count}")
                        print(f"   Solutions tried: {len(self.solution_history)}")
                        self.solved = True
                        return True
                    else:
                        print("\n⚠️ Final verification failed - continuing...")
                else:
                    consecutive_failures += 1
                    print(f"\n❌ Solution #{i}: FAILED")
                    all_failed_commands.extend(failed_cmds)
            
            # All solutions failed - trigger web search consultation
            if not success_count and HAS_AI:
                print(f"\n{'='*70}")
                print(f"⚠️ ALL SOLUTIONS FAILED (Consecutive: {consecutive_failures})")
                print(f"{'='*70}")
                
                if consecutive_failures >= 3:
                    print("\n🚨 Multiple consecutive failures detected")
                    print("   Triggering deep web search consultation...")
                
                # Trigger AI web search
                ai_response = self.trigger_web_search_consultation(
                    all_failed_commands,
                    original_issue
                )
                
                if ai_response and 'recommended_solutions' in ai_response:
                    new_solutions = ai_response['recommended_solutions']
                    new_solutions = [s for s in new_solutions if s.get('solution_type') == 'commands']
                    
                    if new_solutions:
                        print(f"\n✅ AI provided {len(new_solutions)} new web-verified solutions")
                        
                        # Display AI insights
                        if 'root_cause_analysis' in ai_response:
                            print(f"\n📊 Root Cause: {ai_response['root_cause_analysis'][:150]}...")
                        if 'new_strategy' in ai_response:
                            print(f"💡 New Strategy: {ai_response['new_strategy'][:150]}...")
                        if 'web_searches_performed' in ai_response:
                            print(f"🌐 Web Searches: {len(ai_response['web_searches_performed'])} performed")
                        
                        # Display alternative packages if suggested
                        if 'alternative_packages' in ai_response:
                            print("\n📦 Alternative Packages Suggested:")
                            for alt in ai_response['alternative_packages'][:3]:
                                print(f"   {alt.get('original')} → {alt.get('alternative')}")
                                print(f"      Reason: {alt.get('reason', 'N/A')[:80]}...")
                        
                        solutions = new_solutions
                        consecutive_failures = 0
                        print("\n🔄 Continuing with AI-suggested solutions...")
                        time.sleep(2)
                        continue
                    else:
                        print("\n⚠️ AI did not provide command-based solutions")
                else:
                    print("\n❌ AI consultation failed")
                
                # Check if we should continue
                if ai_response and not ai_response.get('should_continue', True):
                    print("\n🛑 AI recommends stopping resolution attempts")
                    if 'next_steps' in ai_response:
                        print(f"   Recommendation: {ai_response['next_steps']}")
                    break
            
            elif not success_count:
                print("\n❌ All solutions failed and no AI assistance available")
                break
        
        # Final status
        print(f"\n{'='*70}")
        print("❌ RESOLUTION INCOMPLETE")
        print(f"{'='*70}")
        print(f"   Total iterations: {iteration}")
        print(f"   AI consultations: {self.ai_consultation_count}")
        print(f"   Web searches performed: {self.web_search_count}")
        print(f"   Solutions attempted: {len(self.solution_history)}")
        print("\n💡 Consider:")
        print("   - Manual intervention may be required")
        print("   - Try a clean virtual environment")
        print("   - Check for system-level dependencies")
        
        return False
    
    def save_execution_log(self, log_path: str = "resolution_log.json"):
        """Save comprehensive execution log"""
        log_data = {
            'json_file': str(self.json_path),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'resolution_status': 'SOLVED' if self.solved else 'INCOMPLETE',
            'ai_consultations': self.ai_consultation_count,
            'web_searches': self.web_search_count,
            'total_commands': len(self.execution_log),
            'successful_commands': sum(1 for log in self.execution_log if log['success']),
            'solution_history': self.solution_history,
            'execution_log': self.execution_log
        }
        
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n📝 Execution log saved to {log_path}")


def main():
    """Main entry point - fully automatic with continuous learning"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI-Powered Automatic Package Conflict Resolver v2.0'
    )
    parser.add_argument(
        'json_file',
        nargs='?',
        default='exectest1.json',
        help='Conflict analysis JSON file (default: exectest1.json)'
    )
    parser.add_argument(
        '--max-ai-iterations',
        type=int,
        default=8,
        help='Max AI consultation attempts (default: 8)'
    )
    parser.add_argument(
        '--log',
        default='resolution_log.json',
        help='Execution log path (default: resolution_log.json)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI assistance (only use JSON solutions)'
    )
    parser.add_argument(
        '--auto-apply',
        action='store_true',
        help='Automatically apply solutions without confirmation'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("🔧 AI-Powered Package Conflict Resolver v2.0")
    print("   Enhanced with Web Search & Continuous Learning")
    print("="*70)
    print("Mode: FULLY AUTOMATIC - Continuous until solved")
    
    if args.no_ai:
        global HAS_AI
        HAS_AI = False
        print("AI assistance: DISABLED")
    elif HAS_AI:
        print("AI assistance: ENABLED")
        print("Web search: ENABLED")
        print("Learning: ENABLED (tracks all attempts)")
    else:
        print("AI assistance: UNAVAILABLE (import failed)")
    
    print("="*70)
    
    resolver = EnhancedAIConflictResolver(
        args.json_file,
        max_ai_iterations=args.max_ai_iterations
    )
    
    success = resolver.continuous_resolution_loop()
    resolver.save_execution_log(args.log)
    
    print("\n" + "="*70)
    if success:
        print("✅ FINAL STATUS: SOLVED")
        print("="*70)
        print("\n🎉 All conflicts resolved successfully!")
        print("📦 Packages are ready to use")
    else:
        print("⚠️ FINAL STATUS: NEEDS ATTENTION")
        print("="*70)
        print("\n💡 Next steps:")
        print("   1. Review resolution_log.json for details")
        print("   2. Check web_search_consultation_*.json for AI findings")
        print("   3. Consider manual intervention or clean environment")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()