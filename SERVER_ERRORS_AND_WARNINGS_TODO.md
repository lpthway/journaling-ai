# Server Errors and Warnings TODO List

**Generated:** August 10, 2025  
**Analysis of:** `backend/server.log`  
**Priority Assessment:** Based on impact on functionality and user experience

---

## 🚨 Critical Issues (Fix Immediately)

### 1. CUDA Device-Side Assert Errors
**Priority: P0 - Critical**
- **Issue:** Multiple CUDA device-side assert triggered errors affecting AI functionality
- **Impact:** AI features completely broken (emotion analysis, crisis detection, vector embeddings)
- **Affected Services:**
  - `ai_intervention_service`: Crisis detection fails
  - `psychology_knowledge_service`: Knowledge search fails
  - `vector_service`: Vector embeddings fail
  - `ai_model_manager`: Model loading fails
- **Error Pattern:** `CUDA error: device-side assert triggered`
- **Solution Options:**
  1. **Force CPU Mode:** Set `CUDA_VISIBLE_DEVICES=""` environment variable
  2. **Debug Mode:** Set `CUDA_LAUNCH_BLOCKING=1` for detailed error tracking
  3. **Model Compatibility:** Switch to CPU-compatible model configurations
  4. **GPU Memory:** Clear GPU memory and restart with smaller models
- **Files to Check:**
  - `backend/app/services/ai_model_manager.py`
  - `backend/app/services/vector_service.py`
  - `backend/app/services/ai_intervention_service.py`

---

## ⚠️ High Priority Issues (Fix This Week)

### 2. Security Configuration Warning
**Priority: P1 - High**
- **Issue:** `No SECURITY_SECRET_KEY environment variable found`
- **Impact:** Security vulnerability, auto-generated keys not persistent
- **Location:** `backend/app/core/config.py:71`
- **Solution:**
  1. Create `.env` file with `SECURITY_SECRET_KEY=<secure-random-key>`
  2. Update production deployment configuration
  3. Add to environment setup documentation

### 3. Zero-Shot Classification Model Configuration
**Priority: P1 - High**
- **Issue:** `Failed to determine 'entailment' label id from the label2id mapping`
- **Impact:** Crisis detection accuracy may be compromised
- **Frequency:** Multiple occurrences during AI processing
- **Solution:**
  1. Update model configuration with proper label mapping
  2. Consider switching to a better-configured zero-shot model
  3. Add custom label mapping in model initialization

### 4. Database Performance Issues
**Priority: P1 - High**
- **Issue:** Slow database operations (1.010s, 0.128s warnings)
- **Impact:** Poor user experience, performance target violations
- **Pattern:** `🐌 Slow database operation` warnings
- **Solution:**
  1. Optimize database queries and indexes
  2. Review connection pool configuration
  3. Analyze slow query patterns
  4. Consider database performance tuning

---

## 📊 Performance Warnings (Fix This Month)

### 5. Cache Hit Rate Below Target
**Priority: P2 - Medium**
- **Issue:** Cache hit rate consistently below 80% target
- **Current Rates:** 0.00% to 62.79% (target: 80%)
- **Impact:** Increased database load and response times
- **Solution:**
  1. Review caching strategy effectiveness
  2. Adjust cache TTL settings
  3. Implement better cache warming strategies
  4. Consider adjusting performance targets for development

### 6. Performance Target Violations
**Priority: P2 - Medium**
- **Issues:**
  - `cache_hit_rate` consistently missed
  - `db_query_time` frequently exceeded
- **Solution:**
  1. Tune performance monitoring thresholds for development environment
  2. Implement performance optimization strategies
  3. Consider different targets for dev vs production

---

## 🔧 Deprecation Warnings (Fix Next Sprint)

### 7. Transformers Library Deprecations
**Priority: P3 - Low**
- **Issue 1:** `return_all_scores` parameter deprecated
  - **Location:** Text classification pipeline
  - **Solution:** Replace with `top_k=None` or `top_k=1`
- **Issue 2:** `encoder_attention_mask` deprecated (Future warning)
  - **Models Affected:** RobertaSdpaSelfAttention, XLMRobertaSdpaSelfAttention, BertSdpaSelfAttention
  - **Timeline:** Will be removed in version 4.55.0
  - **Solution:** Update model usage to use newer attention mechanisms

---

## 🛡️ Crisis Detection Warnings (Monitor)

### 8. Crisis Intervention Logging
**Priority: P4 - Info**
- **Issue:** Crisis indicators detected for test user
- **Pattern:** `🚨 Crisis indicators detected: ['severe_distress']`
- **Impact:** Expected behavior for test data, but should be monitored
- **Action:** Verify crisis detection is working as intended

---

## 📋 Action Plan

### Immediate Actions (This Week)
1. **Fix CUDA Issues:**
   ```bash
   # Option 1: Force CPU mode
   export CUDA_VISIBLE_DEVICES=""
   
   # Option 2: Debug mode
   export CUDA_LAUNCH_BLOCKING=1
   export TORCH_USE_CUDA_DSA=1
   ```

2. **Set Security Key:**
   ```bash
   echo "SECURITY_SECRET_KEY=$(openssl rand -hex 32)" >> backend/.env
   ```

3. **Model Configuration:**
   - Review and fix zero-shot classification model setup
   - Add proper label mapping for entailment detection

### Next Week
1. **Database Optimization:**
   - Analyze slow queries
   - Optimize connection pooling
   - Review indexing strategy

2. **Performance Tuning:**
   - Adjust cache strategies
   - Update performance monitoring thresholds

### Next Sprint
1. **Dependency Updates:**
   - Update transformers library usage
   - Remove deprecated parameter usage
   - Test with newer model versions

---

## 🔍 Monitoring Recommendations

### Log Monitoring
- Set up alerts for CUDA errors
- Monitor cache hit rate trends
- Track database performance metrics
- Watch for new deprecation warnings

### Health Checks
- Verify AI services functionality after CUDA fixes
- Test crisis detection accuracy
- Validate vector database operations
- Monitor security key persistence

---

## 📝 Notes

- **Test Data Context:** Some warnings (like crisis detection) are expected with test data
- **Development Environment:** Performance targets may need adjustment for dev setup
- **GPU Dependencies:** Consider CPU fallback strategies for deployment flexibility
- **Model Updates:** Plan for transformers library updates to address deprecations

**Last Updated:** August 10, 2025  
**Status:** Ready for prioritization and assignment
