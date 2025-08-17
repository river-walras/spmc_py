import cProfile
import pstats
import io
from main import performance_test

def profile_performance():
    """Profile the SPMC queue performance test"""
    pr = cProfile.Profile()
    
    # Start profiling
    pr.enable()
    performance_test()
    pr.disable()
    
    # Save detailed stats to file
    pr.dump_stats('spmc_profile.prof')
    
    # Print summary to console
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    print(s.getvalue())
    
    # Print stats sorted by total time
    print("\n" + "="*50)
    print("Top functions by total time:")
    print("="*50)
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s)
    ps.sort_stats('tottime')
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())

if __name__ == "__main__":
    profile_performance()