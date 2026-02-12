import argparse
import sys
from src.utils.initialization import (
    read_config_from_yaml,
    seed_everything,
    set_credentials,
    get_out_file,
)
from src.configs import *
from src.reddit.reddit import run_reddit
from src.anonymized.anonymized import (
    run_anonymized,
    run_eval_inference,
    run_utility_scoring,
)
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
            run_reddit(cfg)
        elif cfg.task == Task.ANONYMIZED:
            if cfg.task_config.run_eval_inference:
                run_eval_inference(cfg)
            elif cfg.task_config.run_utility_scoring:
                run_utility_scoring(cfg)
            elif cfg.task_config.anonymizer.anon_type in ["adversarial_llm", "span_llm"]:
                # Adversarial mode - run adversarial loop
                from src.models.model_factory import get_model

                defender = get_model(cfg.task_config.anon_model)
                attacker = get_model(cfg.task_config.attack_model)
                evaluator = get_model(cfg.task_config.evaluator_model)

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
                run_anonymized(cfg)
        else:
            raise NotImplementedError(f"Task {cfg.task} not implemented")

    except ValueError as e:
        sys.stderr.write(f"Error: {e}")
    finally:
        if cfg.store:
            f.close()
