import accel_mtrng

def print_header(title):
    """Helper function for formatted output."""
    print("\n" + "=" * 40)
    print(f"--- {title} ---")
    print("=" * 40)

def main():
    
    print_header("Using Singleton (Global) Functions")

    print(f"Global random integer [1, 100]: {accel_mtrng.get_int(1, 100)}")
    print(f"Global random double [0.0, 1.0): {accel_mtrng.get_real(0.0, 1.0):.4f}")

    my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"\nOriginal list: {my_list}")

    accel_mtrng.shuffle(my_list)
    print(f"List after global shuffle: {my_list}")

    sampled_list = accel_mtrng.sample(my_list, 4)
    print(f"Sampled 4 unique elements: {sampled_list}")
    
    generated_list = accel_mtrng.generate_int_list(size=5, min=1000, max=2000)
    print(f"Generated list of 5 ints: {generated_list}")

    print_header("Using Class Instances for Reproducibility")

    seed = accel_mtrng.LOW_SEED
    print(f"Using a fixed seed: {seed}\n")

    rng_instance_1 = accel_mtrng.MersenneTwister(seed)
    
    print("First sequence from instance 1:")
    for _ in range(5):
        print(f"   - Random int [1, 100]: {rng_instance_1.get_int(1, 100)}")

    rng_instance_2 = accel_mtrng.MersenneTwister(seed)

    print("\nFirst sequence from instance 2 (same seed):")
    for _ in range(5):
        print(f"   - Random int [1, 100]: {rng_instance_2.get_int(1, 100)}")

    print("\nNote: The sequences are identical, proving reproducibility.")
    
    rng_instance_3 = accel_mtrng.MersenneTwister()
    print("\nFirst sequence from instance 3 (default seed):")
    for _ in range(5):
        print(f"   - Random int [1, 100]: {rng_instance_3.get_int(1, 100)}")
    print("\nNote: This sequence is different from the seeded ones.")

if __name__ == "__main__":
    main()

