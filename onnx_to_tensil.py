"""
Compile all models using tensil package, user_specified architecture and onnx
Save :
    - logs of the compilation in a csv file
    - tensil model files (.tmodel, .tarch, .tdata)
"""

import docker
import os
import argparse



def move_file(compiled_model_name, output_path):
    """
    Move tmodel, tprog and tdata to the specified directory
    Args :
        - compiled_model_name (str) : *_onnx_{arch}, correspond to output of tensil
    """
    print("Moving file")

    print(os.getcwd())
    print(compiled_model_name)

    compiled_model_name = compiled_model_name.replace("-", "_")
    print(compiled_model_name)
    # Moving Compiled model
    try :
        os.rename(compiled_model_name + ".tmodel", output_path + compiled_model_name + ".tmodel")
    except :
        print("No tmodel file")
    try :
        os.rename(compiled_model_name + ".tprog", output_path + compiled_model_name + ".tprog")
    except :
        print("No tprog file")
    try :
        os.rename(compiled_model_name + ".tdata", output_path + compiled_model_name + ".tdata")
    except :
        print("No data file")


def save_compilation_result(logs, name, path):
    """
    Save the logs in a csv file
    """
    print("logs in:", path+name+".txt")


    with open(path+name+".txt","wb") as file:

        file.write(logs)



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--onnx-path', type=str, help='path to onnx file', required=True)
    parser.add_argument('--arch-path', type=str, default= "arch/custom_perf.tarch", help='path to tensil architecture file')
    parser.add_argument('--output-dir', type=str, default= "tensil/", help='path to script output directory')
    parser.add_argument('--onnx-output', type=str, default= "Output", help='name of the onnx output layer (better to keep default) (default = Output)')
    args = parser.parse_args()

    # Create output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Network Compilation
    print("Tensil compiling...")

    network = args.onnx_path
    pwd = os.getcwd()
    try:
        client = docker.from_env()
    except docker.errors.DockerException as er:
        raise docker.errors.DockerException("error when initializing docker client, maybe it's not launch ?") from er#
    name_net = network.split(sep="/")
    name_net = name_net[-1][:-5]
    try:
        # - a : architecture
        # - m : onnx model
        # -v  : verbose

        # additional summary (all default to false):
        # -s : print summary
        # --layers-summary
        # --scheduler-summary
        # --partition-summary
        # --strides-summary
        # --instructions-summary

        summary_flags=["-s", "true","--layers-summary","true","--scheduler-summary","true","--partitions-summary","true","--strides-summary","true","--instructions-summary","true"]

        log_casa = client.containers.run("tensilai/tensil:latest",
                                            ["tensil", "compile", "-a", args.arch_path, "-m", network,
                                            "-o", args.onnx_output, "-t", args.output_dir]+summary_flags,
                                            volumes=[pwd + ":/work"],
                                            working_dir="/work",
                                            stderr=True)

        save_compilation_result(log_casa, name_net, args.output_dir)
        print("-------------------------")
        print("-------------------------")
        print("-------------------------")
        print("Compilation successful !!")
        print("-------------------------")
        print("-------------------------")

    except docker.errors.ContainerError as exc:
        with open(args.output_dir + name_net + ".txt","wb") as file:

            file.write(exc.container.logs())
        print("-------------------------")
        print("-------------------------")
        print("-------------------------")
        print("Compilation unsuccessful")
        print("error was: ")
        print("------------------------")
        print(exc.container.logs())
        print("------------------------")

if __name__ == "__main__":
    main()