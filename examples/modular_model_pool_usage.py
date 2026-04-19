"""
Example: Using the Modular Provider Registry

This example demonstrates how to use the provider registry to:
1. Check which providers are available
2. Select models for different roles (defender, attacker, evaluator)
3. Create heterogeneous model compositions
4. Handle unavailability gracefully
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.providers.registry import (
    ProviderRegistry,
    ProviderStatus,
    get_registry,
    print_provider_status
)


def example_1_check_providers():
    """Example 1: Check which providers are available"""
    print("\n" + "="*60)
    print("Example 1: Checking Provider Availability")
    print("="*60)

    # Get registry for international region
    registry = get_registry(region="international")

    # Check all providers
    availability = registry.get_available_providers()

    print(f"\nTotal providers checked: {len(availability)}")
    print(f"Available providers: {sum(1 for a in availability.values() if a.status == ProviderStatus.AVAILABLE)}")
    print(f"Unconfigured providers: {sum(1 for a in availability.values() if a.status == ProviderStatus.UNCONFIGURED)}")

    # Show details for each provider
    for provider_id, avail in availability.items():
        provider_info = registry.get_provider_info(provider_id)
        print(f"\n{provider_info.name}:")
        print(f"  Status: {avail.status.value}")
        if avail.status == ProviderStatus.AVAILABLE:
            print(f"  Available models: {', '.join(avail.available_models)}")
        else:
            print(f"  Issue: {avail.error_message}")


def example_2_select_models_for_roles():
    """Example 2: Select best models for different roles"""
    print("\n" + "="*60)
    print("Example 2: Selecting Models for Different Roles")
    print("="*60)

    registry = get_registry(region="international")

    # Get best defender models
    print("\nBest Defender Models:")
    defender_models = registry.get_available_models(role="defender")
    for i, model in enumerate(defender_models[:3], 1):
        print(f"  {i}. {model.name} ({model.provider_id})")
        print(f"     Score: {model.defender_score:.2f}, Cost: ${model.cost_per_1k_input:.2f}/1k input")

    # Get best attacker models
    print("\nBest Attacker Models:")
    attacker_models = registry.get_available_models(role="attacker")
    for i, model in enumerate(attacker_models[:3], 1):
        print(f"  {i}. {model.name} ({model.provider_id})")
        print(f"     Score: {model.attacker_score:.2f}, Cost: ${model.cost_per_1k_input:.2f}/1k input")

    # Get best evaluator models
    print("\nBest Evaluator Models:")
    evaluator_models = registry.get_available_models(role="evaluator")
    for i, model in enumerate(evaluator_models[:3], 1):
        print(f"  {i}. {model.name} ({model.provider_id})")
        print(f"     Score: {model.evaluator_score:.2f}, Cost: ${model.cost_per_1k_input:.2f}/1k input")


def example_3_heterogeneous_composition():
    """Example 3: Create heterogeneous model composition"""
    print("\n" + "="*60)
    print("Example 3: Creating Heterogeneous Model Composition")
    print("="*60)

    registry = get_registry(region="international")

    # Strategy: Use different providers for each role
    print("\nStrategy: Use different providers for each role")
    print("-" * 60)

    # Select best available model for each role from different providers
    used_providers = set()
    composition = {}

    for role in ["defender", "attacker", "evaluator"]:
        # Get available models for this role
        models = registry.get_available_models(role=role)

        # Find best model from a provider not yet used
        for model in models:
            if model.provider_id not in used_providers:
                composition[role] = model
                used_providers.add(model.provider_id)
                break

        # If no unique provider, use best available
        if role not in composition and models:
            composition[role] = models[0]
            used_providers.add(models[0].provider_id)

    # Show composition
    print("\nRecommended Heterogeneous Composition:")
    for role, model in composition.items():
        print(f"\n{role.upper()}:")
        print(f"  Model: {model.name}")
        print(f"  Provider: {model.provider_id}")
        print(f"  Score: {getattr(model, f'{role}_score'):.2f}")
        print(f"  Cost: ${model.cost_per_1k_input:.2f} input / ${model.cost_per_1k_output:.2f} output per 1k tokens")

    print(f"\nProviders used: {', '.join(used_providers)}")
    print(f"Unique providers: {len(used_providers)}")


def example_4_cost_estimation():
    """Example 4: Estimate costs for an experiment"""
    print("\n" + "="*60)
    print("Example 4: Cost Estimation for Experiment")
    print("="*60)

    registry = get_registry(region="international")

    # Define a sample composition
    composition = {
        "defender": "deepseek-chat",
        "attacker": "deepseek-chat",
        "evaluator": "gpt-4o-mini"
    }

    print("\nSample Composition:")
    for role, model_id in composition.items():
        model_info = registry.get_model_info(model_id)
        if model_info:
            print(f"  {role}: {model_info.name} ({model_info.provider_id})")

    # Estimate costs
    num_profiles = 100
    num_rounds = 5
    avg_tokens_per_call = 1000

    total_cost = 0

    print(f"\nCost Assumptions:")
    print(f"  Profiles: {num_profiles}")
    print(f"  Rounds per profile: {num_rounds}")
    print(f"  Average tokens per call: {avg_tokens_per_call}")

    print(f"\nCost Breakdown:")

    for role, model_id in composition.items():
        model_info = registry.get_model_info(model_id)
        if not model_info:
            continue

        # Estimate calls
        calls = num_profiles * num_rounds
        input_tokens = calls * avg_tokens_per_call
        output_tokens = calls * (avg_tokens_per_call // 2)  # Assume output is half of input

        # Calculate cost
        cost = (
            (input_tokens / 1000) * model_info.cost_per_1k_input +
            (output_tokens / 1000) * model_info.cost_per_1k_output
        )

        total_cost += cost

        print(f"\n  {role.upper()} ({model_info.name}):")
        print(f"    Calls: {calls:,}")
        print(f"    Input tokens: {input_tokens:,}")
        print(f"    Output tokens: {output_tokens:,}")
        print(f"    Cost: ${cost:.2f}")

    print(f"\n  {'='*40}")
    print(f"  TOTAL ESTIMATED COST: ${total_cost:.2f}")
    print(f"  Cost per profile: ${total_cost/num_profiles:.4f}")


def example_5_china_friendly_selection():
    """Example 5: Select models for China region"""
    print("\n" + "="*60)
    print("Example 5: China-Friendly Model Selection")
    print("="*60)

    # Get registry for China region
    registry = get_registry(region="china")

    print("\nProviders Available in China:")
    availability = registry.get_available_providers()

    for provider_id, avail in availability.items():
        provider_info = registry.get_provider_info(provider_id)
        status_symbol = "✓" if avail.status == ProviderStatus.AVAILABLE else "✗"
        print(f"  {status_symbol} {provider_info.name} ({provider_id})")

    # Get best models for each role
    print("\nBest Models Available in China:")
    for role in ["defender", "attacker", "evaluator"]:
        models = registry.get_available_models(role=role)
        if models:
            best = models[0]
            print(f"\n  {role.upper()}: {best.name}")
            print(f"    Provider: {best.provider_id}")
            print(f"    Score: {getattr(best, f'{role}_score'):.2f}")
            print(f"    Cost: ${best.cost_per_1k_input:.2f}/1k input")


def example_6_graceful_degradation():
    """Example 6: Handle unavailable providers gracefully"""
    print("\n" + "="*60)
    print("Example 6: Graceful Degradation")
    print("="*60)

    registry = get_registry(region="international")

    # Try to create instances with fallback
    print("\nAttempting to create model instances with fallback:")

    # List of preferred models in order
    preferred_models = [
        "gpt-4o",           # OpenAI (may not be available)
        "claude-3-5-sonnet-20241022",  # Anthropic (may not be available)
        "deepseek-chat",    # DeepSeek (may not be available)
        "llama3.1-70b"      # Ollama (may not be installed)
    ]

    for model_id in preferred_models:
        model_info = registry.get_model_info(model_id)
        if not model_info:
            print(f"\n  {model_id}: Model info not found")
            continue

        availability = registry.check_provider_availability(model_info.provider_id)

        if availability.status == ProviderStatus.AVAILABLE:
            print(f"\n  ✓ {model_id} ({model_info.name}): Available")
            print(f"    Provider: {model_info.provider_id}")
            print(f"    Would create instance here")
            # In real usage, you would call:
            # model = registry.create_model_instance(model_id)
            break
        else:
            print(f"\n  ✗ {model_id} ({model_info.name}): {availability.status.value}")
            print(f"    Reason: {availability.error_message}")
            print(f"    Trying next model...")


if __name__ == "__main__":
    # Run all examples
    print("\n" + "="*70)
    print(" MODULAR PROVIDER REGISTRY - USAGE EXAMPLES")
    print("="*70)

    # Check provider status first
    print("\n--- Initial Provider Status Check ---")
    print_provider_status(region="international")

    # Run examples
    example_1_check_providers()
    example_2_select_models_for_roles()
    example_3_heterogeneous_composition()
    example_4_cost_estimation()
    example_5_china_friendly_selection()
    example_6_graceful_degradation()

    print("\n" + "="*70)
    print(" Examples completed!")
    print("="*70)
