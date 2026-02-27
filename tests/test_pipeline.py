import sys
import os
import pytest
from kfp import compiler

# Add pipeline directory to path so we can import the pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../pipeline")))
from pipeline import continous_model_training_deployment_pipeline

def test_pipeline_compilation(tmp_path):
    """
    Test that the KFP pipeline DAG compiles successfully.
    This validates the syntax, component connections, and type hints of the DSL.
    """
    compiled_pipeline_path = tmp_path / "pipeline.yaml"
    
    # Attempt to compile the pipeline
    try:
        compiler.Compiler().compile(
            pipeline_func=continous_model_training_deployment_pipeline,
            package_path=str(compiled_pipeline_path)
        )
    except Exception as e:
        pytest.fail(f"Pipeline failed to compile: {str(e)}")
        
    # Verify the file was created and isn't empty
    assert compiled_pipeline_path.exists()
    assert compiled_pipeline_path.stat().st_size > 0
    
    # Basic check to ensure it looks like a valid KFP YAML
    content = compiled_pipeline_path.read_text()
    assert "pipelineInfo" in content
    assert "name: continuous-model-training-deployment" in content
