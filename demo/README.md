# 0xhacked CTF demo


## How to Deploy Challenges
1. build the docker image and launch
2. create a `dynamic_zkp` challenge in hte CTFd
3. create a `Flag`, write the `check` function


## How to Play Challenges
1. write your Exploit Contract
2. test your Contract with `foundry`
3. generate the ZKP with `zkProver`, like `zkProver evm -r <RPC_HOST> -b <BLOCK_NUMBER> Exploit.sol:Exploit`
4. upload the `proof.bin`

## Thanks
- [paradigm-ctf-2022](https://github.com/paradigmxyz/paradigm-ctf-2022/)
- [paradigm-ctf-infrastructure](https://github.com/paradigmxyz/paradigm-ctf-infrastructure)