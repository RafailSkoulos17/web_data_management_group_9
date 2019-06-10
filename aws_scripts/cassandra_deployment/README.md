## Cassanrda deployment

This directory contains all the files needed for the creation of the Cassandra cluster.
The implementation was inspired by [this](https://medium.com/devoops-and-universe/my-first-cassandra-cluster-deployment-on-aws-using-cloudformation-35840c7c8ebf?fbclid=IwAR0ZtZGpxfOSgBiSz6z2GVKVGsCdgp6yBd8gEqntLszU_mOZnUdf8HWW1Ew)
article.

### Cluster structure
 The main VPC contains 3 public subnets in 3 different availability zones. 
 Each of these subnets contains 1 seed node
 and 5 non-seed nodes. Therefore, the cluster contains in total 18 nodes. 
 The seed nodes are *i3en.xlarge* nodes while the non-seed ones are 
 *m4.large* instances. 
  Furthermore, The non-seed nodes are contained into a Auto 
 Scaling group which ensure that Cassandra has always the right amount of nodes.
  

### Prerequisites

 Before following the procedure described below to create the Cassandra cluster, you should have installed 
 *Packer*, *AWS CLI* and *Ansible*.

### Procedure

1. Run *packer build Packerfile.txt* to build the AMI of the Cassandra nodes
2. Run *aws cloudformation create-stack --stack-name CassandraCloudFormationTemplate — template-body file://CassandraCloudFormationTemplate.json*
to create the cluster.

