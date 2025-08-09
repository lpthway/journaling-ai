#!/usr/bin/env python3
"""
Performance testing script for optimization validation
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTest:
    """Performance testing utility"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    async def time_request(self, client: httpx.AsyncClient, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Time a single HTTP request"""
        start_time = time.time()
        try:
            response = await client.request(method, url, **kwargs)
            end_time = time.time()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'payload_size': len(response.content) if response.content else 0,
                'headers': dict(response.headers)
            }
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'error': str(e),
                'response_time': end_time - start_time,
                'payload_size': 0
            }
    
    async def run_multiple_requests(
        self, 
        client: httpx.AsyncClient,
        method: str, 
        url: str, 
        count: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Run multiple requests and calculate statistics"""
        logger.info(f"Running {count} requests to {method} {url}")
        
        tasks = [
            self.time_request(client, method, url, **kwargs)
            for _ in range(count)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        response_times = [r['response_time'] for r in results if r['success']]
        payload_sizes = [r['payload_size'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])
        
        if response_times:
            stats = {
                'total_requests': count,
                'successful_requests': success_count,
                'success_rate': (success_count / count) * 100,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'avg_payload_size': statistics.mean(payload_sizes) if payload_sizes else 0,
                'total_payload_size': sum(payload_sizes)
            }
        else:
            stats = {
                'total_requests': count,
                'successful_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'errors': [r['error'] for r in results if not r['success']]
            }
        
        return stats
    
    async def test_endpoint_comparison(
        self,
        client: httpx.AsyncClient,
        test_name: str,
        original_endpoint: str,
        optimized_endpoint: str,
        request_count: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Compare performance between original and optimized endpoints"""
        logger.info(f"Testing {test_name}: Original vs Optimized")
        
        # Test original endpoint
        original_stats = await self.run_multiple_requests(
            client, 'GET', original_endpoint, request_count, **kwargs
        )
        
        # Test optimized endpoint
        optimized_stats = await self.run_multiple_requests(
            client, 'GET', optimized_endpoint, request_count, **kwargs
        )
        
        # Calculate improvement
        if original_stats['success_rate'] > 0 and optimized_stats['success_rate'] > 0:
            response_time_improvement = (
                (original_stats['avg_response_time'] - optimized_stats['avg_response_time']) /
                original_stats['avg_response_time'] * 100
            )
            
            payload_size_reduction = 0
            if original_stats.get('avg_payload_size', 0) > 0:
                payload_size_reduction = (
                    (original_stats['avg_payload_size'] - optimized_stats.get('avg_payload_size', 0)) /
                    original_stats['avg_payload_size'] * 100
                )
        else:
            response_time_improvement = 0
            payload_size_reduction = 0
        
        comparison = {
            'test_name': test_name,
            'original': original_stats,
            'optimized': optimized_stats,
            'improvement': {
                'response_time_improvement_percent': round(response_time_improvement, 2),
                'payload_size_reduction_percent': round(payload_size_reduction, 2),
                'meets_20_percent_target': response_time_improvement >= 20.0
            }
        }
        
        self.results[test_name] = comparison
        return comparison
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        logger.info("Starting comprehensive performance tests")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Entry list loading
            await self.test_endpoint_comparison(
                client,
                "Entry List Loading",
                f"{self.base_url}/api/v1/entries/?limit=20",
                f"{self.base_url}/api/v1/performance/entries/lightweight?limit=20&include_content=false",
                request_count=15
            )
            
            # Test 2: Search functionality
            await self.test_endpoint_comparison(
                client,
                "Search Performance",
                f"{self.base_url}/api/v1/entries/search/semantic?query=test&limit=10",
                f"{self.base_url}/api/v1/performance/search/fast?query=test&limit=10",
                request_count=10
            )
            
            # Test 3: Insights/mood stats
            await self.test_endpoint_comparison(
                client,
                "Mood Statistics",
                f"{self.base_url}/api/v1/insights/mood-stats?days=30",
                f"{self.base_url}/api/v1/performance/insights/mood-stats-optimized?days=30",
                request_count=10
            )
            
            # Test 4: Topics with counts
            await self.test_endpoint_comparison(
                client,
                "Topics Loading",
                f"{self.base_url}/api/v1/topics/",
                f"{self.base_url}/api/v1/performance/topics/with-counts",
                request_count=10
            )
        
        # Calculate overall performance
        overall_improvement = self.calculate_overall_improvement()
        
        summary = {
            'overall_improvement': overall_improvement,
            'detailed_results': self.results,
            'recommendation': self.generate_recommendation(overall_improvement)
        }
        
        return summary
    
    def calculate_overall_improvement(self) -> Dict[str, float]:
        """Calculate overall performance improvement across all tests"""
        improvements = []
        payload_reductions = []
        
        for test_name, result in self.results.items():
            improvement = result['improvement']
            if improvement['response_time_improvement_percent'] > 0:
                improvements.append(improvement['response_time_improvement_percent'])
            if improvement['payload_size_reduction_percent'] > 0:
                payload_reductions.append(improvement['payload_size_reduction_percent'])
        
        overall = {
            'avg_response_time_improvement': statistics.mean(improvements) if improvements else 0,
            'avg_payload_reduction': statistics.mean(payload_reductions) if payload_reductions else 0,
            'tests_meeting_target': sum(1 for _, result in self.results.items() 
                                      if result['improvement']['meets_20_percent_target']),
            'total_tests': len(self.results)
        }
        
        overall['target_achievement_rate'] = (
            (overall['tests_meeting_target'] / overall['total_tests'] * 100)
            if overall['total_tests'] > 0 else 0
        )
        
        return overall
    
    def generate_recommendation(self, overall_improvement: Dict[str, float]) -> str:
        """Generate recommendation based on performance results"""
        avg_improvement = overall_improvement['avg_response_time_improvement']
        target_rate = overall_improvement['target_achievement_rate']
        
        if avg_improvement >= 20 and target_rate >= 75:
            return "✅ EXCELLENT: Performance optimizations exceed targets. Ready for production deployment."
        elif avg_improvement >= 15 and target_rate >= 50:
            return "🟡 GOOD: Significant performance improvements achieved. Consider additional optimizations."
        elif avg_improvement >= 10:
            return "🟠 MODERATE: Some performance gains achieved. Additional optimization recommended."
        else:
            return "🔴 NEEDS WORK: Performance gains below expectations. Review optimization strategies."

async def main():
    """Main test runner"""
    logger.info("🚀 Starting performance optimization validation")
    
    tester = PerformanceTest()
    
    try:
        results = await tester.run_performance_tests()
        
        # Print results
        print("\n" + "="*60)
        print("PERFORMANCE TEST RESULTS")
        print("="*60)
        
        overall = results['overall_improvement']
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Average Response Time Improvement: {overall['avg_response_time_improvement']:.2f}%")
        print(f"   Average Payload Size Reduction: {overall['avg_payload_reduction']:.2f}%")
        print(f"   Tests Meeting 20% Target: {overall['tests_meeting_target']}/{overall['total_tests']}")
        print(f"   Target Achievement Rate: {overall['target_achievement_rate']:.1f}%")
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   {results['recommendation']}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in results['detailed_results'].items():
            improvement = result['improvement']
            print(f"\n   {test_name}:")
            print(f"      Response Time Improvement: {improvement['response_time_improvement_percent']:.2f}%")
            print(f"      Payload Size Reduction: {improvement['payload_size_reduction_percent']:.2f}%")
            print(f"      Meets Target: {'✅' if improvement['meets_20_percent_target'] else '❌'}")
        
        # Save detailed results
        with open('performance_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: performance_test_results.json")
        
        print("\n" + "="*60)
        
        # Return success/failure based on targets
        if overall['avg_response_time_improvement'] >= 20:
            print("🎉 SUCCESS: Performance optimization target achieved!")
            return True
        else:
            print("⚠️  WARNING: Performance optimization target not fully achieved")
            return False
    
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        print(f"❌ ERROR: Performance tests failed - {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)