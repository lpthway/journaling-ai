# AI Services Testing Strategy

## Overview

Comprehensive testing strategy for AI Services Infrastructure ensuring reliability, performance, and safety of AI-powered journaling capabilities. Testing covers unit tests, integration tests, performance validation, and AI model quality assurance.

## Testing Architecture

### Testing Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    AI Model Quality Tests                   │
├─────────────────────────────────────────────────────────────┤
│ • Model Output Validation    • Bias Detection              │
│ • Confidence Score Accuracy  • Safety Compliance           │
│ • Response Time Benchmarks   • Cultural Sensitivity        │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Integration Tests                          │
├─────────────────────────────────────────────────────────────┤
│ • Service Registry Integration • Cache Performance         │
│ • Cross-Service Communication  • Error Propagation         │
│ • Phase 2 Compatibility       • Health Check Validation    │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     Unit Tests                             │
├─────────────────────────────────────────────────────────────┤
│ • Individual Service Logic    • Memory Management          │
│ • Model Loading Functions     • Error Handling             │
│ • Configuration Validation    • Hardware Detection         │
└─────────────────────────────────────────────────────────────┘
```

## Unit Testing

### AI Model Manager Tests

#### File: `tests/services/test_ai_model_manager.py`
```python
import pytest
import torch
from unittest.mock import Mock, patch
from app.services.ai_model_manager import AIModelManager, ModelType

class TestAIModelManager:
    
    @pytest.fixture
    def model_manager(self):
        return AIModelManager()
    
    def test_hardware_detection(self, model_manager):
        """Test GPU/CPU detection logic"""
        hardware_info = model_manager.detect_hardware()
        
        assert 'gpu_available' in hardware_info
        assert 'gpu_memory_gb' in hardware_info
        assert 'cpu_cores' in hardware_info
        assert isinstance(hardware_info['gpu_available'], bool)
    
    def test_memory_estimation(self, model_manager):
        """Test model memory requirement estimation"""
        for model_type in ModelType:
            memory_estimate = model_manager.estimate_memory_requirement(model_type)
            assert memory_estimate > 0
            assert memory_estimate < 20  # Reasonable upper bound
    
    @patch('torch.cuda.is_available')
    def test_model_loading_gpu_unavailable(self, mock_cuda, model_manager):
        """Test graceful fallback when GPU unavailable"""
        mock_cuda.return_value = False
        
        model = model_manager.load_model(ModelType.EMOTION_ANALYSIS)
        assert model is not None
        # Verify CPU device usage
    
    def test_model_caching(self, model_manager):
        """Test model caching behavior"""
        # First load
        model1 = model_manager.load_model(ModelType.EMOTION_ANALYSIS)
        
        # Second load should return cached model
        model2 = model_manager.load_model(ModelType.EMOTION_ANALYSIS)
        
        assert model1 is model2  # Same instance
    
    def test_memory_limit_enforcement(self, model_manager):
        """Test memory limit enforcement"""
        with patch.object(model_manager, 'get_available_memory') as mock_memory:
            mock_memory.return_value = 1.0  # Low memory
            
            with pytest.raises(MemoryError):
                model_manager.load_model(ModelType.TEXT_GENERATION_LARGE)
    
    def test_model_status_reporting(self, model_manager):
        """Test model status reporting"""
        # Load a model
        model_manager.load_model(ModelType.EMOTION_ANALYSIS)
        
        status = model_manager.get_model_status()
        
        assert 'loaded_models' in status
        assert 'total_memory_usage' in status
        assert 'gpu_available' in status
        assert len(status['loaded_models']) == 1
```

### AI Emotion Service Tests

#### File: `tests/services/test_ai_emotion_service.py`
```python
import pytest
from unittest.mock import Mock, patch
from app.services.ai_emotion_service import AIEmotionService, EmotionAnalysisResult

class TestAIEmotionService:
    
    @pytest.fixture
    def emotion_service(self):
        return AIEmotionService()
    
    def test_basic_emotion_analysis(self, emotion_service):
        """Test basic emotion detection"""
        text = "I'm feeling really happy today!"
        
        result = emotion_service.analyze_emotion(text)
        
        assert isinstance(result, EmotionAnalysisResult)
        assert result.primary_emotion in ['joy', 'happiness', 'positive']
        assert 0 <= result.confidence_score <= 1
    
    def test_crisis_emotion_detection(self, emotion_service):
        """Test detection of concerning emotions"""
        crisis_texts = [
            "I don't see the point in anything anymore",
            "Nobody would miss me if I was gone",
            "I can't handle this pain anymore"
        ]
        
        for text in crisis_texts:
            result = emotion_service.analyze_emotion(text)
            
            # Should detect negative emotions with high confidence
            assert result.primary_emotion in ['sadness', 'despair', 'negative']
            assert result.confidence_score > 0.7
    
    def test_pattern_detection(self, emotion_service):
        """Test emotional pattern detection"""
        # Simulate multiple entries over time
        entries = [
            "Feeling stressed about work",
            "Another difficult day at the office", 
            "Work is overwhelming me again"
        ]
        
        patterns = []
        for entry in entries:
            result = emotion_service.analyze_emotion(entry, context={'history': patterns})
            patterns.append(result)
        
        # Should detect recurring stress pattern
        final_result = patterns[-1]
        assert 'stress_pattern' in final_result.patterns_detected
    
    def test_cultural_adaptation(self, emotion_service):
        """Test cultural emotion interpretation"""
        text = "I need to save face in this situation"
        context = {'cultural_background': 'collectivist'}
        
        result = emotion_service.analyze_emotion(text, context)
        
        assert 'cultural_adaptation' in result.__dict__
        # Should recognize cultural context of 'face' concept
    
    def test_caching_behavior(self, emotion_service):
        """Test emotion analysis caching"""
        text = "I'm feeling anxious about tomorrow"
        
        # First analysis
        result1 = emotion_service.analyze_emotion(text)
        
        # Second analysis should use cache
        with patch.object(emotion_service, '_run_ai_analysis') as mock_analysis:
            result2 = emotion_service.analyze_emotion(text)
            mock_analysis.assert_not_called()  # Should use cache
        
        assert result1.primary_emotion == result2.primary_emotion
    
    def test_confidence_scoring(self, emotion_service):
        """Test confidence score accuracy"""
        # Clear emotional expressions should have high confidence
        clear_text = "I am extremely happy and joyful!"
        clear_result = emotion_service.analyze_emotion(clear_text)
        
        # Ambiguous text should have lower confidence
        ambiguous_text = "It's fine, I guess"
        ambiguous_result = emotion_service.analyze_emotion(ambiguous_text)
        
        assert clear_result.confidence_score > ambiguous_result.confidence_score
        assert clear_result.confidence_score > 0.8
        assert ambiguous_result.confidence_score < 0.6
```

### AI Intervention Service Tests

#### File: `tests/services/test_ai_intervention_service.py`
```python
import pytest
from unittest.mock import Mock, patch
from app.services.ai_intervention_service import AIInterventionService, CrisisLevel

class TestAIInterventionService:
    
    @pytest.fixture
    def intervention_service(self):
        return AIInterventionService()
    
    def test_low_risk_assessment(self, intervention_service):
        """Test low-risk situation handling"""
        text = "Had a tough day but looking forward to the weekend"
        context = {'user_history': 'stable'}
        
        assessment = intervention_service.assess_crisis_indicators(text, context)
        
        assert assessment.crisis_level == CrisisLevel.LOW
        assert not assessment.requires_professional_referral
        assert len(assessment.immediate_actions) == 0
    
    def test_high_risk_assessment(self, intervention_service):
        """Test high-risk crisis detection"""
        crisis_text = "I've been thinking about ending it all"
        context = {'user_history': 'concerning_patterns'}
        
        assessment = intervention_service.assess_crisis_indicators(crisis_text, context)
        
        assert assessment.crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]
        assert assessment.requires_professional_referral
        assert len(assessment.immediate_actions) > 0
        assert any('crisis' in action.lower() for action in assessment.immediate_actions)
    
    def test_intervention_template_selection(self, intervention_service):
        """Test appropriate intervention template selection"""
        scenarios = [
            ("mild_anxiety", "I'm feeling a bit worried"),
            ("moderate_depression", "I've been feeling down for weeks"),
            ("crisis_situation", "I don't want to be here anymore")
        ]
        
        for scenario_type, text in scenarios:
            assessment = intervention_service.assess_crisis_indicators(text, {})
            
            # Verify intervention matches crisis level
            if assessment.crisis_level == CrisisLevel.CRITICAL:
                assert any('immediate' in intervention.lower() 
                          for intervention in assessment.recommended_interventions)
    
    def test_safety_resource_provision(self, intervention_service):
        """Test safety resource recommendations"""
        crisis_text = "I need help but don't know where to turn"
        
        assessment = intervention_service.assess_crisis_indicators(crisis_text, {})
        
        assert len(assessment.safety_resources) > 0
        assert any('hotline' in resource.lower() or 'crisis' in resource.lower() 
                  for resource in assessment.safety_resources)
    
    def test_false_positive_handling(self, intervention_service):
        """Test handling of potential false positives"""
        # Text that might trigger false alarms
        false_positive_texts = [
            "This movie killed me with laughter",  # Metaphorical 'killed'
            "I'm dying to see the new restaurant",  # Metaphorical 'dying'
            "Work is suicide; so busy this week"   # Metaphorical 'suicide'
        ]
        
        for text in false_positive_texts:
            assessment = intervention_service.assess_crisis_indicators(text, {})
            
            # Should not trigger crisis protocols for metaphorical language
            assert assessment.crisis_level <= CrisisLevel.MEDIUM
    
    @patch('app.services.ai_intervention_service.send_crisis_alert')
    def test_crisis_alert_system(self, mock_alert, intervention_service):
        """Test crisis alert system activation"""
        critical_text = "I have a plan to hurt myself tonight"
        
        assessment = intervention_service.assess_crisis_indicators(critical_text, {})
        
        if assessment.crisis_level == CrisisLevel.CRITICAL:
            mock_alert.assert_called_once()
```

## Integration Testing

### Service Registry Integration

#### File: `tests/integration/test_service_registry_integration.py`
```python
import pytest
from app.services.ai_service_init import initialize_ai_services
from app.core.service_interfaces import service_registry

class TestServiceRegistryIntegration:
    
    def test_full_service_initialization(self):
        """Test complete AI service initialization"""
        result = initialize_ai_services()
        
        assert result['status'] == 'success'
        assert len(result['services_initialized']) == 4
        assert len(result['services_failed']) == 0
        assert result['service_registry_status'] == 'healthy'
    
    def test_service_discovery(self):
        """Test service discovery through registry"""
        # Initialize services
        initialize_ai_services()
        
        # Test each service is discoverable
        ai_services = [
            'ai_model_manager',
            'ai_prompt_service', 
            'ai_emotion_service',
            'ai_intervention_service'
        ]
        
        for service_name in ai_services:
            service = service_registry.get_service(service_name)
            assert service is not None
            assert hasattr(service, '__class__')
    
    def test_cross_service_communication(self):
        """Test communication between AI services"""
        initialize_ai_services()
        
        # Get services
        emotion_service = service_registry.get_service('ai_emotion_service')
        intervention_service = service_registry.get_service('ai_intervention_service')
        
        # Test cross-service workflow
        text = "I'm feeling overwhelmed and hopeless"
        
        # Emotion analysis
        emotion_result = emotion_service.analyze_emotion(text)
        
        # Use emotion result in intervention assessment
        context = {'emotion_analysis': emotion_result}
        intervention_result = intervention_service.assess_crisis_indicators(text, context)
        
        # Verify coherent results
        if emotion_result.primary_emotion in ['sadness', 'despair']:
            assert intervention_result.crisis_level >= CrisisLevel.MEDIUM
```

### Cache Integration Tests

#### File: `tests/integration/test_cache_integration.py`
```python
import pytest
from app.services.ai_emotion_service import ai_emotion_service
from app.core.cache_service import unified_cache

class TestCacheIntegration:
    
    def test_emotion_analysis_caching(self):
        """Test emotion analysis result caching"""
        text = "I'm having a wonderful day!"
        
        # Clear cache
        unified_cache.clear()
        
        # First analysis - should cache result
        result1 = ai_emotion_service.analyze_emotion(text)
        
        # Verify cache entry exists
        cache_key = ai_emotion_service._generate_cache_key(text)
        cached_result = unified_cache.get(cache_key)
        assert cached_result is not None
        
        # Second analysis - should use cache
        result2 = ai_emotion_service.analyze_emotion(text)
        
        # Results should be identical
        assert result1.primary_emotion == result2.primary_emotion
        assert result1.confidence_score == result2.confidence_score
    
    def test_cache_invalidation(self):
        """Test cache invalidation on context changes"""
        text = "I feel uncertain about things"
        
        # Analysis with different contexts should not use same cache
        result1 = ai_emotion_service.analyze_emotion(text, context={'mood': 'anxious'})
        result2 = ai_emotion_service.analyze_emotion(text, context={'mood': 'calm'})
        
        # Different contexts may yield different interpretations
        # At minimum, cache keys should be different
        key1 = ai_emotion_service._generate_cache_key(text, {'mood': 'anxious'})
        key2 = ai_emotion_service._generate_cache_key(text, {'mood': 'calm'})
        assert key1 != key2
    
    def test_cache_performance(self):
        """Test cache performance improvement"""
        import time
        
        text = "This is a test for cache performance measurement"
        
        # Clear cache
        unified_cache.clear()
        
        # Measure uncached analysis time
        start_time = time.time()
        result1 = ai_emotion_service.analyze_emotion(text)
        uncached_time = time.time() - start_time
        
        # Measure cached analysis time
        start_time = time.time()
        result2 = ai_emotion_service.analyze_emotion(text)
        cached_time = time.time() - start_time
        
        # Cached should be significantly faster
        assert cached_time < uncached_time * 0.1  # At least 10x faster
        assert result1.primary_emotion == result2.primary_emotion
```

## Performance Testing

### Response Time Benchmarks

#### File: `tests/performance/test_response_times.py`
```python
import pytest
import time
import statistics
from app.services.ai_emotion_service import ai_emotion_service
from app.services.ai_prompt_service import ai_prompt_service

class TestResponseTimes:
    
    def test_emotion_analysis_response_time(self):
        """Test emotion analysis response time requirements"""
        texts = [
            "I'm feeling great today!",
            "This has been a challenging week for me.",
            "I'm not sure how I feel about this situation.",
            "Everything seems to be going wrong lately.",
            "I'm excited about the future possibilities."
        ]
        
        response_times = []
        
        for text in texts:
            start_time = time.time()
            result = ai_emotion_service.analyze_emotion(text)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Individual response should be reasonable
            assert response_time < 5.0  # 5 seconds max
            assert result is not None
        
        # Average response time should be good
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 2.0  # 2 seconds average
    
    def test_cached_response_time(self):
        """Test cached response performance"""
        text = "Performance test for cached responses"
        
        # First call (uncached)
        start_time = time.time()
        result1 = ai_emotion_service.analyze_emotion(text)
        uncached_time = time.time() - start_time
        
        # Second call (cached)
        start_time = time.time()
        result2 = ai_emotion_service.analyze_emotion(text)
        cached_time = time.time() - start_time
        
        # Cached should be much faster
        assert cached_time < 0.1  # Under 100ms for cached
        assert cached_time < uncached_time * 0.2  # At least 5x faster
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent AI requests"""
        import threading
        import queue
        
        def analyze_emotion_worker(text, result_queue):
            try:
                start_time = time.time()
                result = ai_emotion_service.analyze_emotion(text)
                end_time = time.time()
                
                result_queue.put({
                    'success': True,
                    'response_time': end_time - start_time,
                    'result': result
                })
            except Exception as e:
                result_queue.put({
                    'success': False,
                    'error': str(e)
                })
        
        # Create multiple concurrent requests
        texts = [f"Concurrent test message {i}" for i in range(10)]
        threads = []
        result_queue = queue.Queue()
        
        # Start all threads
        for text in texts:
            thread = threading.Thread(target=analyze_emotion_worker, args=(text, result_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # Verify all succeeded
        assert len(results) == len(texts)
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == len(texts)
        
        # Verify reasonable response times even under load
        avg_response_time = statistics.mean([r['response_time'] for r in successful_results])
        assert avg_response_time < 10.0  # 10 seconds under concurrent load
```

### Memory Usage Tests

#### File: `tests/performance/test_memory_usage.py`
```python
import pytest
import psutil
import torch
from app.services.ai_model_manager import ai_model_manager, ModelType

class TestMemoryUsage:
    
    def test_memory_usage_tracking(self):
        """Test memory usage stays within limits"""
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1e9  # GB
        
        # Load models
        models_loaded = []
        for model_type in [ModelType.EMOTION_ANALYSIS, ModelType.TEXT_GENERATION]:
            model = ai_model_manager.load_model(model_type)
            models_loaded.append(model)
            
            # Check memory after each model
            current_memory = process.memory_info().rss / 1e9
            memory_increase = current_memory - baseline_memory
            
            # Should not exceed reasonable limits
            assert memory_increase < 8.0  # 8GB max increase
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1e9
        total_increase = final_memory - baseline_memory
        
        # Log memory usage for monitoring
        print(f"Memory usage increase: {total_increase:.2f}GB")
    
    def test_gpu_memory_management(self):
        """Test GPU memory management if available"""
        if not torch.cuda.is_available():
            pytest.skip("GPU not available")
        
        # Clear GPU cache
        torch.cuda.empty_cache()
        baseline_gpu = torch.cuda.memory_allocated() / 1e9
        
        # Load GPU models
        model = ai_model_manager.load_model(ModelType.EMOTION_ANALYSIS)
        
        # Check GPU memory usage
        current_gpu = torch.cuda.memory_allocated() / 1e9
        gpu_increase = current_gpu - baseline_gpu
        
        # Should respect GPU memory limits
        gpu_total = torch.cuda.get_device_properties(0).total_memory / 1e9
        assert gpu_increase < gpu_total * 0.8  # Use max 80% of GPU memory
    
    def test_memory_cleanup(self):
        """Test memory cleanup functionality"""
        # Load several models
        models = []
        for model_type in ModelType:
            try:
                model = ai_model_manager.load_model(model_type)
                models.append(model)
            except Exception:
                pass  # Skip if model unavailable
        
        # Get memory usage
        process = psutil.Process()
        pre_cleanup_memory = process.memory_info().rss / 1e9
        
        # Trigger cleanup
        ai_model_manager.cleanup_unused_models()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Check memory after cleanup
        post_cleanup_memory = process.memory_info().rss / 1e9
        
        # Memory should not increase significantly
        memory_change = post_cleanup_memory - pre_cleanup_memory
        assert abs(memory_change) < 1.0  # Less than 1GB change
```

## AI Model Quality Tests

### Model Output Validation

#### File: `tests/quality/test_model_outputs.py`
```python
import pytest
from app.services.ai_emotion_service import ai_emotion_service
from app.services.ai_prompt_service import ai_prompt_service, PromptType

class TestModelQuality:
    
    def test_emotion_detection_accuracy(self):
        """Test emotion detection accuracy on known cases"""
        test_cases = [
            ("I'm so happy and excited!", ["joy", "happiness", "excitement"]),
            ("I feel completely overwhelmed and sad", ["sadness", "overwhelm", "negative"]),
            ("This makes me really angry", ["anger", "frustration", "negative"]),
            ("I'm terrified about what might happen", ["fear", "anxiety", "worry"]),
            ("I feel so grateful and blessed", ["gratitude", "positive", "contentment"])
        ]
        
        correct_predictions = 0
        
        for text, expected_emotions in test_cases:
            result = ai_emotion_service.analyze_emotion(text)
            
            # Check if detected emotion matches expected
            if any(emotion in result.primary_emotion.lower() for emotion in expected_emotions):
                correct_predictions += 1
            
            # Confidence should be reasonable for clear cases
            assert result.confidence_score > 0.6
        
        # Should get most cases right
        accuracy = correct_predictions / len(test_cases)
        assert accuracy >= 0.8  # 80% accuracy minimum
    
    def test_prompt_generation_quality(self):
        """Test generated prompt quality"""
        context = {
            'user_mood': 'reflective',
            'time_of_day': 'evening',
            'recent_entries': ['work stress', 'family time']
        }
        
        for prompt_type in PromptType:
            generated = ai_prompt_service.generate_prompt(prompt_type, context)
            
            # Quality checks
            assert len(generated.content) > 20  # Substantial content
            assert len(generated.content) < 500  # Not too verbose
            assert generated.confidence_score > 0.5  # Reasonable confidence
            
            # Content appropriateness
            content_lower = generated.content.lower()
            if prompt_type == PromptType.REFLECTION:
                assert any(word in content_lower for word in ['reflect', 'think', 'consider'])
            elif prompt_type == PromptType.GRATITUDE:
                assert any(word in content_lower for word in ['grateful', 'appreciate', 'thankful'])
    
    def test_bias_detection(self):
        """Test for potential bias in AI outputs"""
        # Test gender bias
        gender_test_cases = [
            ("I work as a nurse", "nursing"),
            ("I work as an engineer", "engineering"), 
            ("I'm taking care of my children", "childcare")
        ]
        
        for text, domain in gender_test_cases:
            result = ai_emotion_service.analyze_emotion(text)
            
            # Should not make assumptions based on gender stereotypes
            # This is a basic check - more sophisticated bias testing would be needed
            assert result.primary_emotion not in ['invalid', 'biased']
            assert result.confidence_score > 0
    
    def test_crisis_detection_sensitivity(self):
        """Test crisis detection sensitivity and specificity"""
        # True positive cases (should detect crisis)
        crisis_cases = [
            "I don't want to live anymore",
            "Nobody would care if I disappeared", 
            "I have a plan to hurt myself",
            "Everything is hopeless and pointless"
        ]
        
        # True negative cases (should not detect crisis)
        normal_cases = [
            "I had a bad day but I'll get through it",
            "Feeling stressed but working on solutions",
            "Things are tough but I have support",
            "Disappointed but optimistic about tomorrow"
        ]
        
        from app.services.ai_intervention_service import ai_intervention_service, CrisisLevel
        
        # Test sensitivity (detecting real crises)
        crisis_detected = 0
        for text in crisis_cases:
            assessment = ai_intervention_service.assess_crisis_indicators(text, {})
            if assessment.crisis_level >= CrisisLevel.HIGH:
                crisis_detected += 1
        
        sensitivity = crisis_detected / len(crisis_cases)
        assert sensitivity >= 0.8  # 80% sensitivity minimum
        
        # Test specificity (not false alarms)
        false_alarms = 0
        for text in normal_cases:
            assessment = ai_intervention_service.assess_crisis_indicators(text, {})
            if assessment.crisis_level >= CrisisLevel.HIGH:
                false_alarms += 1
        
        specificity = 1 - (false_alarms / len(normal_cases))
        assert specificity >= 0.8  # 80% specificity minimum
```

## Test Execution Framework

### Continuous Integration Setup

#### File: `.github/workflows/ai-services-tests.yml`
```yaml
name: AI Services Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.13]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        pip install transformers sentence-transformers psutil
        pip install pytest pytest-cov pytest-asyncio
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        pytest tests/services/ -v --cov=app.services
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v -m "not slow"
    
    - name: Run AI quality tests
      run: |
        pytest tests/quality/ -v --timeout=300
    
    - name: Generate coverage report
      run: |
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Local Testing Commands

```bash
# Run all AI service tests
pytest tests/ -v

# Run specific test categories
pytest tests/services/ -v          # Unit tests
pytest tests/integration/ -v       # Integration tests
pytest tests/performance/ -v       # Performance tests
pytest tests/quality/ -v           # AI quality tests

# Run with coverage
pytest tests/ --cov=app.services --cov-report=html

# Run performance tests only
pytest tests/performance/ -v -m "performance"

# Run critical safety tests
pytest tests/quality/test_model_outputs.py::TestModelQuality::test_crisis_detection_sensitivity -v

# Run specific service tests
pytest tests/services/test_ai_emotion_service.py -v
```

### Test Data Management

#### File: `tests/fixtures/test_data.py`
```python
import pytest

@pytest.fixture
def emotion_test_data():
    """Standard emotion test cases"""
    return {
        'positive': [
            "I'm feeling fantastic today!",
            "This is the best day ever!",
            "I'm so grateful for everything",
            "Feeling blessed and happy"
        ],
        'negative': [
            "I'm feeling really down today",
            "Everything seems hopeless",
            "I can't handle this anymore",
            "Feeling overwhelmed and sad"
        ],
        'neutral': [
            "Today was an ordinary day",
            "Not much happening today",
            "Things are okay, I suppose",
            "Just another regular day"
        ],
        'crisis': [
            "I don't want to be here anymore",
            "Nobody would miss me",
            "I have thoughts of hurting myself",
            "Life feels completely pointless"
        ]
    }

@pytest.fixture
def prompt_generation_contexts():
    """Standard contexts for prompt generation testing"""
    return [
        {
            'user_mood': 'anxious',
            'time_of_day': 'morning',
            'recent_entries': ['work stress']
        },
        {
            'user_mood': 'grateful', 
            'time_of_day': 'evening',
            'recent_entries': ['family time', 'achievement']
        },
        {
            'user_mood': 'reflective',
            'time_of_day': 'night',
            'recent_entries': ['life changes', 'decisions']
        }
    ]
```

This comprehensive testing strategy ensures AI services are reliable, performant, safe, and provide high-quality outputs for journaling users while maintaining enterprise-grade standards.
