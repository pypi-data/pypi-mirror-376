# sdk/whispey/whispey.py
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from whispey.event_handlers import setup_session_event_handlers, safe_extract_transcript_data
from whispey.metrics_service import setup_usage_collector, create_session_data
from whispey.send_log import send_to_whispey
from whispey.evaluation_integration import evaluation_runner

logger = logging.getLogger("observe_session")

# Global session storage - store data, not class instances
_session_data_store = {}


def observe_session(session, agent_id, host_url, bug_detector=None, enable_otel=False, otel_endpoint=None, telemetry_instance=None, eval=None, **kwargs):
    session_id = str(uuid.uuid4())
    
    try:        
        # Setup session data and usage collector using your existing functions
        usage_collector = setup_usage_collector()
        session_data = create_session_data(
            type('MockContext', (), {'room': type('MockRoom', (), {'name': session_id})})(), 
            time.time()
        )
        
        if telemetry_instance:
            session_data['telemetry_instance'] = telemetry_instance
        
        # Update session data with all dynamic parameters
        session_data.update(kwargs)
        
        # Setup evaluation if specified
        evaluation_type = eval
        
        # Store session info in global storage (data only, not class instances)
        _session_data_store[session_id] = {
            'start_time': time.time(),
            'session_data': session_data,
            'usage_collector': usage_collector,
            'dynamic_params': kwargs,
            'agent_id': agent_id,
            'call_active': True,
            'whispey_data': None,
            'bug_detector': bug_detector,
            'telemetry_instance': telemetry_instance,  # Store telemetry instance
            'evaluation_type': evaluation_type
        }
        
        # Setup telemetry if enabled
        if enable_otel and telemetry_instance:
            telemetry_instance._setup_telemetry(session_id)
        
        # Setup event handlers with session
        setup_session_event_handlers(session, session_data, usage_collector, None, bug_detector)
        
        # Add custom handlers for Whispey integration
        @session.on("disconnected")
        def on_disconnected(event):
            end_session_manually(session_id, "disconnected")
        
        @session.on("close")
        def on_session_close(event):
            error_msg = str(event.error) if hasattr(event, 'error') and event.error else None
            end_session_manually(session_id, "completed", error_msg)
        
        return session_id
        
    except Exception as e:
        logger.error(f"⚠️ Failed to set up metrics collection: {e}")
        # Still return session_id so caller can handle gracefully
        return session_id

def generate_whispey_data(session_id: str, status: str = "in_progress", error: str = None) -> Dict[str, Any]:
    """Generate Whispey data for a session"""
    if session_id not in _session_data_store:
        logger.error(f"Session {session_id} not found in data store")
        return {}
    
    session_info = _session_data_store[session_id]
    current_time = time.time()
    start_time = session_info['start_time']
    
    # Extract transcript data using your existing function
    session_data = session_info['session_data']
    if session_data:
        try:
            safe_extract_transcript_data(session_data)
        except Exception as e:
            logger.error(f"Error extracting transcript data: {e}")
    
    # Get usage summary
    usage_summary = {}
    usage_collector = session_info['usage_collector']
    if usage_collector:
        try:
            summary = usage_collector.get_summary()
            usage_summary = {
                "llm_prompt_tokens": getattr(summary, 'llm_prompt_tokens', 0),
                "llm_completion_tokens": getattr(summary, 'llm_completion_tokens', 0),
                "llm_cached_tokens": getattr(summary, 'llm_prompt_cached_tokens', 0),
                "tts_characters": getattr(summary, 'tts_characters_count', 0),
                "stt_audio_duration": getattr(summary, 'stt_audio_duration', 0.0)
            }
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
    
    # Calculate duration
    duration = int(current_time - start_time)
    
    # Prepare Whispey format data
    # Exclude phone identifiers from metadata
    dynamic_params: Dict[str, Any] = session_info['dynamic_params'] or {}
    sanitized_dynamic_params = {
        k: v for k, v in dynamic_params.items()
        if k not in {"phone_number", "customer_number", "phone"}
    }

    # FIXED: Define whispey_data at function level, not inside if block
    whispey_data = {
        "call_id": f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "agent_id": session_info['agent_id'],
        "customer_number": session_info['dynamic_params'].get('phone_number', 'unknown'),
        "call_ended_reason": status,
        "call_started_at": start_time,
        "call_ended_at": current_time,
        "transcript_type": "agent",
        "recording_url": "",  # Will be filled by caller
        "transcript_json": [],
        "transcript_with_metrics": [],
        "metadata": {
            "usage": usage_summary,
            "duration_formatted": f"{duration // 60}m {duration % 60}s",
            "complete_configuration": session_data.get('complete_configuration') if session_data else None,
            **sanitized_dynamic_params  # Include dynamic parameters without phone identifiers
        }
    }
    
    # Add transcript data if available
    if session_data:
        transcript_data = session_data.get("transcript_with_metrics", [])
        
        # Ensure trace fields are included in each turn
        enhanced_transcript = []
        for turn in transcript_data:
            # Verify configuration exists
            if not turn.get('turn_configuration'):
                logger.warning(f"Turn {turn.get('turn_id', 'unknown')} missing configuration!")
                # Try to inject from session level as fallback
                turn['turn_configuration'] = session_data.get('complete_configuration')
            
            # Add trace fields to each turn if they exist
            enhanced_turn = {
                **turn,  # All existing fields
                'trace_id': turn.get('trace_id'),
                'otel_spans': turn.get('otel_spans', []),
                'tool_calls': turn.get('tool_calls', []),
                'trace_duration_ms': turn.get('trace_duration_ms'),
                'trace_cost_usd': turn.get('trace_cost_usd')
            }
            enhanced_transcript.append(enhanced_turn)
        
        whispey_data["transcript_with_metrics"] = enhanced_transcript
        
        # Extract transcript_json from session history if available
        if hasattr(session_data, 'history'):
            try:
                whispey_data["transcript_json"] = session_data.history.to_dict().get("items", [])
            except Exception as e:
                logger.debug(f"Could not extract transcript_json from history: {e}")
        
        # Try other possible transcript locations
        if not whispey_data["transcript_json"]:
            for attr in ['transcript_data', 'conversation_history', 'messages']:
                if hasattr(session_data, attr):
                    try:
                        data = getattr(session_data, attr)
                        if isinstance(data, list):
                            whispey_data["transcript_json"] = data
                            break
                        elif hasattr(data, 'to_dict'):
                            whispey_data["transcript_json"] = data.to_dict().get("items", [])
                            break
                    except Exception as e:
                        logger.debug(f"Could not extract transcript from {attr}: {e}")

        # Add bug report data if available
        if 'bug_reports' in session_data:
            whispey_data["metadata"]["bug_reports"] = session_data['bug_reports']
        if 'bug_flagged_turns' in session_data:
            whispey_data["metadata"]["bug_flagged_turns"] = session_data['bug_flagged_turns']
        
        # Note: Evaluation is now handled asynchronously in the background
        # to prevent blocking the main session shutdown process
    
    return whispey_data

def get_session_whispey_data(session_id: str) -> Dict[str, Any]:
    """Get Whispey-formatted data for a session"""
    if session_id not in _session_data_store:
        logger.error(f"Session {session_id} not found")
        return {}
    
    session_info = _session_data_store[session_id]
    
    # Return cached data if session has ended
    if not session_info['call_active'] and session_info['whispey_data']:
        return session_info['whispey_data']
    
    # Generate fresh data
    return generate_whispey_data(session_id)

def end_session_manually(session_id: str, status: str = "completed", error: str = None):
    """Manually end a session"""
    if session_id not in _session_data_store:
        logger.error(f"Session {session_id} not found for manual end")
        return
    
    logger.info(f"🔚 Manually ending session {session_id} with status: {status}")
    
    # Mark as inactive
    _session_data_store[session_id]['call_active'] = False
    
    # Generate and cache final whispey data
    final_data = generate_whispey_data(session_id, status, error)
    _session_data_store[session_id]['whispey_data'] = final_data
    
    logger.info(f"📊 Session {session_id} ended - Whispey data prepared")

def cleanup_session(session_id: str):
    """Clean up session data"""
    if session_id in _session_data_store:
        del _session_data_store[session_id]
        logger.info(f"🗑️ Cleaned up session {session_id}")






def categorize_span(span_name: str) -> str:
    """Categorize span by operation type for easier filtering"""
    if not span_name:
        return "other"
        
    name_lower = span_name.lower()
    
    if any(x in name_lower for x in ['llm_request', 'llm_node', 'llm']):
        return "llm"
    elif any(x in name_lower for x in ['tts_request', 'tts_node', 'tts']):
        return "tts"
    elif any(x in name_lower for x in ['stt_request', 'stt_node', 'stt']):
        return "stt"
    elif 'function_tool' in name_lower or 'tool' in name_lower:
        return "tool"
    elif 'user_turn' in name_lower or 'user_speaking' in name_lower:
        return "user_interaction"
    elif 'assistant_turn' in name_lower or 'agent_speaking' in name_lower:
        return "assistant_interaction"
    elif 'session' in name_lower:
        return "session_management"
    else:
        return "other"

def calculate_duration_ms(span) -> float:
    """Calculate span duration in milliseconds"""
    try:
        start_time = span.get('start_time', 0)
        end_time = span.get('end_time', 0)
        
        if start_time and end_time and end_time > start_time:
            # Assume timestamps are in nanoseconds, convert to milliseconds
            return (end_time - start_time) / 1_000_000
        
        # Fallback to duration if available
        duration = span.get('duration', 0)
        if duration > 0:
            return duration * 1000  # Convert seconds to milliseconds
            
        return 0
    except Exception:
        return 0

def extract_key_attributes(span) -> dict:
    """Extract only the most important attributes for analysis"""
    try:
        attributes = span.get('attributes', {})
        
        # Handle string attributes (sometimes they're stringified)
        if isinstance(attributes, str):
            try:
                import json
                attributes = json.loads(attributes)
            except:
                return {}
        
        if not isinstance(attributes, dict):
            return {}
        
        # Extract key attributes that are useful for analysis
        key_attrs = {}
        important_keys = [
            'session_id', 'lk.user_transcript', 'lk.response.text', 
            'gen_ai.request.model', 'lk.speech_id', 'lk.interrupted',
            'gen_ai.usage.input_tokens', 'gen_ai.usage.output_tokens',
            'lk.tts.streaming', 'lk.input_text', 'model_name',
            'prompt_tokens', 'completion_tokens', 'characters_count',
            'audio_duration', 'request_id', 'error'
        ]
        
        for key in important_keys:
            if key in attributes:
                key_attrs[key] = attributes[key]
        
        return key_attrs
    except Exception:
        return {}

def generate_span_id(span) -> str:
    """Generate a unique span ID"""
    try:
        # Try to use existing span_id or create one
        if 'span_id' in span:
            return str(span['span_id'])
        
        # Generate from name and timestamp
        name = span.get('name', 'unknown')
        timestamp = span.get('start_time', time.time())
        return f"span_{name}_{int(timestamp)}"[:64]  # Limit length
    except Exception:
        return f"span_unknown_{int(time.time())}"

def extract_trace_id(span) -> str:
    """Extract trace ID from span"""
    try:
        if 'trace_id' in span:
            return str(span['trace_id'])
        
        # Check in attributes
        attributes = span.get('attributes', {})
        if isinstance(attributes, dict) and 'trace_id' in attributes:
            return str(attributes['trace_id'])
        
        return None
    except Exception:
        return None

def build_critical_path(spans) -> list:
    """Build the critical path of main conversation flow"""
    try:
        if not spans:
            return []
        
        critical_spans = []
        
        # Sort spans by start time
        sorted_spans = sorted(spans, key=lambda x: x.get('start_time', 0))
        
        # Focus on main conversation flow operations
        for span in sorted_spans:
            operation_type = span.get('operation_type', 'other')
            if operation_type in ['user_interaction', 'assistant_interaction', 'llm', 'tts', 'stt', 'tool']:
                critical_spans.append({
                    "name": span.get('name', 'unknown'),
                    "operation_type": operation_type,
                    "duration_ms": span.get('duration_ms', 0),
                    "start_time": span.get('start_time', 0)
                })
        
        return critical_spans
    except Exception as e:
        logger.error(f"Error building critical path: {e}")
        return []


def structure_telemetry_data(session_id: str) -> Dict[str, Any]:
    """Structure telemetry spans data for better analysis - PRESERVE ALL ORIGINAL DATA"""
    try:
        telemetry_data = {
            "session_traces": [],
            "performance_metrics": {
                "total_spans": 0,
                "avg_llm_latency": 0,
                "avg_tts_latency": 0,
                "avg_stt_latency": 0,
                "total_tool_calls": 0
            },
            "span_summary": {
                "by_operation": {},
                "by_turn": {},
                "critical_path": []
            }
        }
        
        if session_id not in _session_data_store:
            return telemetry_data
            
        session_info = _session_data_store[session_id]
        telemetry_instance = session_info.get('telemetry_instance')
        
        if not telemetry_instance or not hasattr(telemetry_instance, 'spans_data'):
            return telemetry_data
            
        spans = telemetry_instance.spans_data
        if not spans:
            return telemetry_data
                    
        operation_counts = {}
        latency_sums = {"llm": [], "tts": [], "stt": [], "tool": []}
        
        # PRESERVE ALL ORIGINAL SPAN DATA - don't clean/filter
        for span in spans:
            try:
                # Add operation_type categorization but keep everything else
                span_name = span.get('name', 'unknown')
                operation_type = categorize_span(span_name)
                
                # Keep the entire original span, just add our categorization
                enhanced_span = dict(span)  # Copy all original data
                enhanced_span['operation_type'] = operation_type
                enhanced_span['source'] = 'otel_capture'
                
                telemetry_data["session_traces"].append(enhanced_span)
                
                # Collect metrics for summary
                operation_counts[operation_type] = operation_counts.get(operation_type, 0) + 1
                
                # Calculate duration if available
                duration_ms = calculate_duration_ms(span)
                if duration_ms > 0 and operation_type in latency_sums:
                    latency_sums[operation_type].append(duration_ms)
                    
            except Exception as e:
                logger.error(f"Error processing span {span}: {e}")
                continue
        
        # Build summary metrics
        telemetry_data["span_summary"]["by_operation"] = operation_counts
        telemetry_data["performance_metrics"] = {
            "total_spans": len(telemetry_data["session_traces"]),
            "avg_llm_latency": sum(latency_sums["llm"]) / len(latency_sums["llm"]) if latency_sums["llm"] else 0,
            "avg_tts_latency": sum(latency_sums["tts"]) / len(latency_sums["tts"]) if latency_sums["tts"] else 0,
            "avg_stt_latency": sum(latency_sums["stt"]) / len(latency_sums["stt"]) if latency_sums["stt"] else 0,
            "total_tool_calls": operation_counts.get("tool", 0),
            "total_user_interactions": operation_counts.get("user_interaction", 0),
            "total_assistant_interactions": operation_counts.get("assistant_interaction", 0)
        }
        
        # Build critical path (fix the sorting issue)
        try:
            sorted_spans = [s for s in telemetry_data["session_traces"] if s.get('start_time_ns')]
            sorted_spans.sort(key=lambda x: x.get('start_time_ns', 0))
            telemetry_data["span_summary"]["critical_path"] = build_critical_path(sorted_spans)
        except Exception as e:
            logger.error(f"Error building critical path: {e}")
            telemetry_data["span_summary"]["critical_path"] = []
        
        return telemetry_data
        
    except Exception as e:
        logger.error(f"Error structuring telemetry data: {e}")
        return {
            "session_traces": [],
            "performance_metrics": {"total_spans": 0, "avg_llm_latency": 0, "avg_tts_latency": 0, "avg_stt_latency": 0, "total_tool_calls": 0},
            "span_summary": {"by_operation": {}, "by_turn": {}, "critical_path": []}
        }





async def send_session_to_whispey(session_id: str, recording_url: str = "", additional_transcript: list = None, force_end: bool = True, apikey: str = None, api_url: str = None, **extra_data) -> dict:
    """
    Send session data to Whispey API
    
    Args:
        session_id: Session ID to send
        recording_url: URL of the call recording
        additional_transcript: Additional transcript data if needed
        force_end: Whether to force end the session before sending (default: True)
        apikey: Custom API key to use. If not provided, uses WHISPEY_API_KEY environment variable
        api_url: Override the default API URL (e.g., your own host). Defaults to built-in Lambda URL
    
    Returns:
        dict: Response from Whispey API
    """
    logger.info(f"🚀 Starting send_session_to_whispey for {session_id}")
    
    if session_id not in _session_data_store:
        logger.error(f"Session {session_id} not found in data store")
        return {"success": False, "error": "Session not found"}
    
    session_info = _session_data_store[session_id]
    
    # Force end session if requested and still active
    if force_end and session_info['call_active']:
        logger.info(f"🔚 Force ending session {session_id}")
        end_session_manually(session_id, "completed")
    
    # Get whispey data
    whispey_data = get_session_whispey_data(session_id)

    # REPLACE the simple telemetry_spans assignment with structured data
    structured_telemetry = structure_telemetry_data(session_id)
    whispey_data["telemetry_data"] = structured_telemetry

    
    
    if not whispey_data:
        logger.error(f"No whispey data generated for session {session_id}")
        return {"success": False, "error": "No data available"}
    
    # Update with additional data
    if recording_url:
        whispey_data["recording_url"] = recording_url
    
    if additional_transcript:
        whispey_data["transcript_json"] = additional_transcript
    
    
    # Check if evaluation is needed
    evaluation_type = session_info.get('evaluation_type')
    
    if evaluation_type:
        # If evaluation is enabled, send everything asynchronously with evaluation
        logger.info(f"🔄 Starting background {evaluation_type} evaluation for session {session_id}")
        
        # Create background task for complete data sending with evaluation
        import asyncio
        async def background_complete_send():
            try:
                # Run evaluation
                evaluation_result = await run_evaluation_async(session_id, evaluation_type, whispey_data)
                
                # Add evaluation results to the data
                if not evaluation_result.get("error"):
                    if 'metadata' not in whispey_data:
                        whispey_data['metadata'] = {}
                    whispey_data['metadata']['evaluation'] = evaluation_result
                    logger.info(f"✅ Added evaluation results to session data")
                else:
                    logger.error(f"❌ Evaluation failed for session {session_id}: {evaluation_result.get('error')}")
                
                # Send complete data with evaluation
                logger.info(f"📤 Sending complete session data with evaluation to Whispey API...")
                logger.info(f"📊 Data keys: {list(whispey_data.keys())}")
                logger.info(f"📊 Data size: {len(str(whispey_data))} characters")
                
                try:
                    # Add timeout to prevent hanging and use shield to protect from cancellation
                    result = await asyncio.wait_for(
                        asyncio.shield(send_to_whispey(whispey_data, apikey=apikey, api_url=api_url)),
                        timeout=20.0  # Reduced to 20 second timeout
                    )
                    
                    if result.get("success"):
                        logger.info(f"✅ Successfully sent complete session {session_id} with evaluation to Whispey")
                    else:
                        logger.error(f"❌ Whispey API returned failure: {result}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"❌ Timeout sending session {session_id} to Whispey API (20s)")
                    result = {"success": False, "error": "Timeout"}
                except asyncio.CancelledError:
                    logger.warning(f"⚠️ Background task cancelled for session {session_id}, but evaluation completed")
                    # Don't re-raise, let cleanup happen
                    result = {"success": False, "error": "Task cancelled but evaluation completed"}
                except (BrokenPipeError, ConnectionError, OSError) as pipe_error:
                    logger.warning(f"⚠️ Process communication error for session {session_id}: {pipe_error}")
                    # This is expected during process shutdown, don't treat as critical error
                    result = {"success": False, "error": "Process communication closed"}
                except Exception as send_error:
                    logger.error(f"❌ Error sending session {session_id} to Whispey API: {send_error}")
                    result = {"success": False, "error": str(send_error)}
                
                # Cleanup session after complete send
                cleanup_session(session_id)
                logger.info(f"🗑️ Cleaned up session {session_id} after complete send")
                    
            except Exception as e:
                logger.error(f"❌ Background complete send failed for session {session_id}: {e}")
                # Still cleanup on error
                cleanup_session(session_id)
        
        # Start background task with proper task management
        task = asyncio.create_task(background_complete_send())
        
        # Store the task so it can be awaited if needed
        if session_id in _session_data_store:
            _session_data_store[session_id]['background_task'] = task
            
        # Add task cleanup callback to handle process shutdown gracefully
        def cleanup_task_on_shutdown():
            if not task.done():
                logger.info(f"🔄 Cancelling background task for session {session_id} due to process shutdown")
                task.cancel()
        
        # Store cleanup callback
        if session_id in _session_data_store:
            _session_data_store[session_id]['cleanup_callback'] = cleanup_task_on_shutdown
        
        # Return immediately without waiting
        return {"success": True, "message": "Session data will be sent asynchronously with evaluation"}
        
    else:
        # No evaluation needed, send data immediately
        try:
            logger.info(f"📤 Sending to Whispey API...")
            result = await send_to_whispey(whispey_data, apikey=apikey, api_url=api_url)
            
            if result.get("success"):
                logger.info(f"✅ Successfully sent session {session_id} to Whispey")
                cleanup_session(session_id)
            else:
                logger.error(f"❌ Whispey API returned failure: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Exception sending to Whispey: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}






# Utility functions
def get_latest_session():
    """Get the most recent session data"""
    if _session_data_store:
        latest_id = max(_session_data_store.keys(), key=lambda x: _session_data_store[x]['start_time'])
        return latest_id, _session_data_store[latest_id]
    return None, None

def get_all_active_sessions():
    """Get all active session IDs"""
    return [sid for sid, data in _session_data_store.items() if data['call_active']]

def cleanup_all_sessions():
    """Clean up all sessions"""
    session_ids = list(_session_data_store.keys())
    for session_id in session_ids:
        # Call cleanup callback if it exists
        if session_id in _session_data_store:
            session_info = _session_data_store[session_id]
            if 'cleanup_callback' in session_info:
                try:
                    session_info['cleanup_callback']()
                except Exception as e:
                    logger.warning(f"⚠️ Error calling cleanup callback for session {session_id}: {e}")
        
        end_session_manually(session_id, "cleanup")
        cleanup_session(session_id)
    logger.info(f"🗑️ Cleaned up {len(session_ids)} sessions")

async def wait_for_all_background_tasks():
    """Wait for all background tasks to complete before shutdown"""
    import asyncio
    
    tasks = []
    for session_id, session_info in _session_data_store.items():
        if 'background_task' in session_info:
            task = session_info['background_task']
            if not task.done():
                tasks.append(task)
                logger.info(f"⏳ Waiting for background task for session {session_id}")
    
    if tasks:
        logger.info(f"⏳ Waiting for {len(tasks)} background tasks to complete...")
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=60.0)
            logger.info(f"✅ All background tasks completed")
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Timeout waiting for background tasks, cancelling remaining tasks")
            for task in tasks:
                if not task.done():
                    task.cancel()
        except Exception as e:
            logger.error(f"❌ Error waiting for background tasks: {e}")
    else:
        logger.info(f"✅ No background tasks to wait for")

async def run_evaluation_async(session_id: str, evaluation_type: str, whispey_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run evaluation asynchronously in the background with timeout protection"""
    try:
        logger.info(f"🔄 Starting async {evaluation_type} evaluation for session {session_id}")
        
        # Prepare conversation data for evaluation
        call_started = whispey_data.get('call_started_at', 0)
        call_ended = whispey_data.get('call_ended_at', 0)
        
        # Ensure we have numeric values for duration calculation
        try:
            if isinstance(call_started, str):
                call_started = float(call_started)
            if isinstance(call_ended, str):
                call_ended = float(call_ended)
            duration = call_ended - call_started
        except (ValueError, TypeError):
            duration = 0
        
        conversation_data = {
            'transcript': whispey_data.get("transcript_with_metrics", []),
            'response_text': '',  # Will be filled from transcript
            'context': {
                'agent_id': whispey_data.get('agent_id'),
                'session_id': session_id,
                'duration': duration
            }
        }
        
        # Extract the last assistant response for evaluation
        if conversation_data['transcript']:
            for turn in reversed(conversation_data['transcript']):
                if turn.get('role') == 'assistant' and turn.get('content'):
                    conversation_data['response_text'] = turn['content']
                    break
        
        # Run evaluation with timeout protection using asyncio
        try:
            logger.info(f"⏱️ Starting {evaluation_type} evaluation with 45s timeout for session {session_id}")
            
            # Use asyncio.wait_for to add timeout protection
            evaluation_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    evaluation_runner.run_evaluation, 
                    evaluation_type, 
                    conversation_data
                ),
                timeout=45.0  # 45 second timeout for evaluation
            )
            
            logger.info(f"⏱️ {evaluation_type} evaluation completed within timeout for session {session_id}")
            
            if evaluation_result:
                logger.info(f"✅ {evaluation_type} evaluation completed for session {session_id}")
                return evaluation_result
            else:
                logger.warning(f"⚠️ {evaluation_type} evaluation returned no results for session {session_id}")
                return {"error": "No evaluation results", "overall_score": 0.0, "evaluation_type": evaluation_type}
                
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ {evaluation_type} evaluation timed out for session {session_id} after 45 seconds")
            return {"error": "Evaluation timeout", "overall_score": 0.0, "evaluation_type": evaluation_type}
        except Exception as eval_error:
            logger.error(f"❌ Evaluation execution error for session {session_id}: {eval_error}")
            return {"error": str(eval_error), "overall_score": 0.0, "evaluation_type": evaluation_type}
            
    except Exception as e:
        logger.error(f"❌ Error running async {evaluation_type} evaluation for session {session_id}: {e}")
        return {"error": str(e), "overall_score": 0.0, "evaluation_type": evaluation_type}

async def send_evaluation_results(session_id: str, evaluation_result: Dict[str, Any], apikey: str = None, api_url: str = None) -> dict:
    """Send evaluation results as an update to the main session data"""
    try:
        logger.info(f"📤 Sending evaluation results for session {session_id}")
        
        # Get the original session data and add evaluation results
        if session_id in _session_data_store:
            session_info = _session_data_store[session_id]
            original_whispey_data = session_info.get('whispey_data', {})
            
            # Add evaluation results to the original data
            if 'metadata' not in original_whispey_data:
                original_whispey_data['metadata'] = {}
            original_whispey_data['metadata']['evaluation'] = evaluation_result
            
            # Send the complete updated session data
            result = await send_to_whispey(original_whispey_data, apikey=apikey, api_url=api_url)
            
            if result.get("success"):
                logger.info(f"✅ Successfully sent evaluation results for session {session_id}")
            else:
                logger.error(f"❌ Failed to send evaluation results for session {session_id}: {result}")
            
            return result
        else:
            logger.error(f"❌ Session {session_id} not found for evaluation update")
            return {"success": False, "error": "Session not found"}
        
    except Exception as e:
        logger.error(f"❌ Exception sending evaluation results for session {session_id}: {e}")
        return {"success": False, "error": str(e)}

def set_evaluation_type(eval_type: str):
    """
    Set the evaluation type for sessions
    
    Args:
        eval_type: Type of evaluation to run. Supported types:
            - "healthbench" - Standard HealthBench evaluation
            - "healthbench_hard" - HealthBench hard subset
            - "healthbench_consensus" - HealthBench consensus subset
    
    Example:
        set_evaluation_type("healthbench")
    """
    global _current_evaluation_type
    _current_evaluation_type = eval_type
    logger.info(f"Evaluation type set to: {eval_type}")

def get_available_evaluations():
    """Get list of available evaluation types"""
    return [
        "healthbench",
        "healthbench_hard", 
        "healthbench_consensus"
    ]

# Global variable to store current evaluation type
_current_evaluation_type = None

def debug_session_state(session_id: str = None):
    """Debug helper to check session state"""
    if session_id:
        if session_id in _session_data_store:
            data = _session_data_store[session_id]
            print(f"Session {session_id}:")
            print(f"  - Active: {data['call_active']}")
            print(f"  - Start time: {datetime.fromtimestamp(data['start_time'])}")
            print(f"  - Has session_data: {data['session_data'] is not None}")
            print(f"  - Has usage_collector: {data['usage_collector'] is not None}")
            print(f"  - Dynamic params: {data['dynamic_params']}")
            print(f"  - Has cached whispey_data: {data['whispey_data'] is not None}")
            print(f"  - Evaluation type: {data.get('evaluation_type', 'None')}")
        else:
            print(f"Session {session_id} not found")
    else:
        print(f"Total sessions: {len(_session_data_store)}")
        for sid, data in _session_data_store.items():
            print(f"  {sid}: active={data['call_active']}, agent={data['agent_id']}, eval={data.get('evaluation_type', 'None')}")