import argparse
import sys
from src.utils.initialization import (
    read_config_from_yaml,
    seed_everything,
    set_credentials,
    get_out_file,
)
from src.configs import *

# Import these only when needed to avoid transformers dependency
def get_reddit_module():
    from src.reddit.reddit import run_reddit
    return run_reddit

def get_anonymized_module():
    from src.anonymized.anonymized import (
        run_anonymized,
        run_eval_inference,
        run_utility_scoring,
    )
    return run_anonymized, run_eval_inference, run_utility_scoring

from src.anonymized.adversarial import run_adversarial_anonymization

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        type=str,
        default="configs/acs_config.yaml",
        help="Path to the config file",
    )
    args = parser.parse_args()

    cfg = read_config_from_yaml(args.config_path)
    seed_everything(cfg.seed)
    set_credentials(cfg)

    f, path = get_out_file(cfg)

    try:
        print(cfg)
        if cfg.task == Task.REDDIT:
            run_reddit = get_reddit_module()
            run_reddit(cfg)
        elif cfg.task == Task.ANONYMIZED:
            run_anonymized, run_eval_inference, run_utility_scoring = get_anonymized_module()
            if cfg.task_config.run_eval_inference:
                run_eval_inference(cfg)
            elif cfg.task_config.run_utility_scoring:
                run_utility_scoring(cfg)
            elif cfg.task_config.anonymizer.anon_type in ["adversarial_llm", "span_llm"]:
                # Adversarial mode - run adversarial loop
                # Use modular provider registry to avoid transformers dependency
                from src.models.providers.registry import get_registry

                registry = get_registry(region="china")

                # Create model instances using registry
                defender = registry.create_model_instance(
                    cfg.task_config.anon_model.name,
                    **cfg.task_config.anon_model.args
                )
                attacker = registry.create_model_instance(
                    cfg.task_config.attack_model.name,
                    **cfg.task_config.attack_model.args
                )
                evaluator = registry.create_model_instance(
                    cfg.task_config.evaluator_model.name,
                    **cfg.task_config.evaluator_model.args
                )

                if not all([defender, attacker, evaluator]):
                    raise ValueError("Failed to create model instances. Check API keys and model names.")

                # Load profiles
                from src.anonymized.anonymized import load_profiles
                profiles = load_profiles(cfg.task_config)

                results = run_adversarial_anonymization(
                    profiles=profiles,
                    defender_model=defender,
                    attacker_model=attacker,
                    evaluator_model=evaluator,
                    config=cfg.task_config,
                    max_rounds=cfg.task_config.max_rounds,
                )

                # Save results
                import json
                import os
                os.makedirs(cfg.task_config.outpath, exist_ok=True)

                output_path = f"{cfg.task_config.outpath}/adversarial_results.jsonl"
                with open(output_path, "w") as f:
                    for profile_id, profile_results in results.items():
                        # Convert to serializable format
                        profile_dict = {
                            "profile_id": profile_id,
                            "results": [
                                {
                                    "round": r.round_num,
                                    "anonymized_text": r.anonymized_text,
                                    "attack_guess": r.attack_guess,
                                    "attack_success": r.attack_success,
                                    "utility_score": r.utility_score,
                                    "privacy_score": r.privacy_score,
                                    "improvement_feedback": r.improvement_feedback,
                                }
                                for r in profile_results
                            ]
                        }
                        f.write(json.dumps(profile_dict) + "\n")

                print(f"Adversarial anonymization results saved to {output_path}")
            else:
                run_anonymized, _, _ = get_anonymized_module()
                run_anonymized(cfg)
        else:
            raise NotImplementedError(f"Task {cfg.task} not implemented")

    except ValueError as e:
        sys.stderr.write(f"Error: {e}")
    finally:
        if cfg.store:
            f.close()
