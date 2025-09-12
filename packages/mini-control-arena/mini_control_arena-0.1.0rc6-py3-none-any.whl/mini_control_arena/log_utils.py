"""Log format conversion utilities for Mini Control Arena."""

import json
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from inspect_ai.log import read_eval_log
from collections import Counter


def convert_log(
    log_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    format: str = "easy_jsonl"
) -> List[Dict[str, Any]]:
    """
    Convert Mini Control Arena evaluation logs to different formats.
    
    Args:
        log_path: Path to the evaluation log file (.eval or .json)
        output_path: Optional path to save the output file. If None, returns data only
        format: Output format (default: "easy_jsonl" for complete trajectory export)
    
    Returns:
        List of dictionaries containing sample data
        
    Example:
        ```python
        from mini_control_arena import convert_log
        
        # Convert to easy_jsonl format (default)
        data = convert_log(
            "logs/eval_20250107.eval",
            output_path="trajectories.easy_jsonl"
        )
        print(f"Exported {len(data)} samples")
        ```
    """
    log = read_eval_log(str(log_path))
    
    if format == "easy_jsonl":
        converted_data = []
        failed_count = 0
        
        print(f"Processing {len(log.samples)} samples from {log_path}")
        
        for i, sample in enumerate(log.samples):
            # Build messages list
            messages = []
            has_assistant_response = False
            
            for msg in sample.messages:
                message_dict = {}
                
                # Always include role
                message_dict["role"] = msg.role if hasattr(msg, 'role') else 'unknown'
                
                # Track if we have assistant messages
                if message_dict["role"] == "assistant":
                    has_assistant_response = True
                
                # Handle content based on role
                if msg.role == 'tool':
                    # Tool messages store output differently
                    if hasattr(msg, 'content') and msg.content:
                        message_dict["content"] = msg.content
                    elif hasattr(msg, 'output'):
                        message_dict["content"] = msg.output
                    elif hasattr(msg, 'text'):
                        message_dict["content"] = msg.text
                    else:
                        message_dict["content"] = "[Tool output not captured]"
                else:
                    # For non-tool messages, use content field
                    if hasattr(msg, 'content'):
                        message_dict["content"] = msg.content if msg.content else ""
                
                # For assistant messages, check for tool calls
                if msg.role == 'assistant' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = []
                    for tool_call in msg.tool_calls:
                        tc = {
                            "function": tool_call.function if hasattr(tool_call, 'function') else 'unknown',
                            "arguments": tool_call.arguments if hasattr(tool_call, 'arguments') else {}
                        }
                        if hasattr(tool_call, 'id'):
                            tc["id"] = tool_call.id
                        tool_calls.append(tc)
                    message_dict["tool_calls"] = tool_calls
                
                messages.append(message_dict)
            
            # Mark incomplete samples
            if not has_assistant_response:
                failed_count += 1
                print(f"  ⚠️ Sample {i} (ID: {sample.id}) has no assistant response recorded")
            
            # Count message types
            message_types = Counter()
            for msg in sample.messages:
                role = msg.role if hasattr(msg, 'role') else 'unknown'
                message_types[role] += 1
            
            # Create sample record
            record = {
                "sample_id": sample.id,
                "sample_index": i,
                "scores": {},
                "messages": messages,
                "metadata": {
                    "total_messages": len(sample.messages),
                    "message_types": dict(message_types),
                    "has_assistant_response": has_assistant_response,
                    "complete": has_assistant_response,
                    "failed": not has_assistant_response
                }
            }
            
            # Add scores with proper extraction
            if hasattr(sample, 'scores') and sample.scores:
                for name, score in sample.scores.items():
                    if hasattr(score, 'value'):
                        record["scores"][name] = score.value
                    else:
                        record["scores"][name] = str(score)
            
            # Add error info if sample failed
            if hasattr(sample, 'error') and sample.error:
                record["metadata"]["error"] = str(sample.error)
            
            converted_data.append(record)
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Total samples: {len(log.samples)}")
        print(f"  Complete samples: {len(log.samples) - failed_count}")
        print(f"  Incomplete samples: {failed_count}")
        
        if failed_count > 0:
            print(f"\n  Note: {failed_count} samples have no assistant responses recorded.")
            print(f"        This may be due to time limits, early termination, or evaluation errors.")
            print(f"        These samples may not have complete trajectories for analysis.")
        
        # Save to JSONL file if output path provided
        if output_path:
            output_file = Path(output_path)
            with open(output_file, 'w') as f:
                for item in converted_data:
                    f.write(json.dumps(item) + '\n')
            print(f"\nSaved to: {output_file}")
        
        return converted_data
    
    else:
        raise ValueError(f"Unsupported format: {format}. Currently only 'easy_jsonl' is supported.")