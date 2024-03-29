#!/bin/bash
#set -xe
#SBATCH -N 1
#SBATCH -t 360

dir=./sam-outputs
dot_dir=$dir/dot
png_dir=$dir/png
taco_exe=./taco/build/bin/taco

KERNEL_NAMES=(
#   tensor3_linear
  # tensor3_fused_feedforward_linear
  # test_max
  # tensor4_mult2_ijklm
  # mul_2
  # gcn_merged
  gcn_1
  gcn_2
  gcn_3
  gcn_4
  # gcn_mul
  # gcn_add
  # add_1
  #tensor4_mult2_jimlk
  # tensor4_mult2_jimlk
  # tensor4_mult2_ikjml
  # tensor3_softmax_multiply2
  # tensor3_fusedlinear1
  # tensor4_mult
  # tensor4_fused
  # tensor3_fused_ffn
  # tensor4_multiply_ijklm
  # tensor4_multiply2_ijklm
  # tensor4_fused_ijklm
)


TACO_ARGS=(
  # "X(i,j,k)=B(i,j,k)*S(i,j) -f=X:sss:0,1,2 -f=M:ss:0,1 -f=D:sss:0,1,2" #reorder: jikl 
  # "X(i,m,k)=(E(m,j)*B(j,l)*C(i,l,k)+E(m,j)*d(j))+f(m)" #-f=X:sss:1,2,0 -f=B:ss:0,1 -f=C:sss:2,0,1 -f=d:s -s=reorder(j,k,i)" #reorder: jikl 
#   "X(i,m,k)=E(m,j)*(B(j,l)*C(i,l,k)+d(j))+f(m)" #-f=X:sss:1,2,0 -f=B:ss:0,1 -f=C:sss:2,0,1 -f=d:s -s=reorder(j,k,i)" #reorder: jikl
#  "X(i,j,k)=exp(B(i,j,k))"
  # "X(i,j,k)=B(j,l)*C(i,l,k)+d(j) -f=X:sss:1,0,2 -f=B:ss:0,1 -f=C:sss:0,1,2 -f=d:s -s=reorder(j,i,k)" #reorder: jikl 
  # "A(i,j,k)=B(j,l)*C(i,l,k) -f=A:sss:1,2,0 -f=B:ss:0,1 -f=C:sss:2,0,1 -s=reorder(j,k,i)" #reorder: jikl 
  # "X(i,j,k)=A(i,j,k)+d(j) -f=X:sss:1,2,0 -f=A:sss:1,2,0 -f=d:s -s=reorder(j,k,i)" #reorder: jikl 

  # "A(j,k)=E(j,i)*F(i,l)*C(l,k) -f=A:ss:0,1 -f=E:ss:0,1 -f=F:ss:1,0 -f=C:ss:1,0 -s=reorder(j,k)" #reorder: jikl 
  # "A(j,k)=E(j,i)*F(i,l)*C(l,k)+d(j) -f=A:ss:0,1 -f=E:ss:0,1 -f=F:ss:1,0 -f=C:ss:1,0 -f=d:s -s=reorder(j,k)" #reorder: jikl 
  # "A(j,k)=E(j,i)*F(i,l)*C(l,k) -f=A:ss -f=E:ss -f=F:ss:1,0 -f=C:ss:1,0" #reorder: jikl 
  "B(i,k)=E(i,l)*F(l,k) -f=B:ss:0,1 -f=E:ss:0,1 -f=F:ss:1,0 -f=d:s -s=reorder(i,k)" #reorder: jikl 
  "A(i,j)=B(i,k)*C(k,j)+d(i) -f=A:ss:0,1 -f=B:ss:0,1 -f=C:ss:1,0 -f=d:s -s=reorder(i,j)" #reorder: jikl 
  "A(i,j)=B(i,k)*E(k,l)*F(l,j)+d(i) -f=A:ss:0,1 -f=B:ss:0,1 -f=E:ss:1,0 -f=F:ss:1,0 -f=d:s -s=reorder(i,j)" #reorder: jikl 
  # "X(i,j)=G(i,k)*E(k,l)*F(l,j)+d(i) -f=A:ss:0,1 -f=B:ss:0,1 -f=E:ss:1,0 -f=F:ss:1,0 -f=d:s -s=reorder(i,j)" #reorder: jikl 

  # "X(m,j)=G(m,n)*I(n,i)*A(i,j)+h(m) -f=X:ss:1,0 -f=G:ss:0,1 -f=I:ss:1,0 -f=A:ss:0,1 -f=h:s -s=reorder(j,m)"
  "X(m,j)=G(m,n)*I(n,i)*B(i,k)*E(k,l)*F(l,j)+h(m) -f=X:ss:0,1 -f=G:ss:0,1 -f=I:ss:1,0 -f=A:ss:0,1 -f=B:ss:1,0 -f=E:ss:1,0 -f=F:ss:1,0 -f=h:s -s=reorder(m,j)"
  # "X(i,j)=B(i,k)*C(k,j) -f=X:ss -f=B:ss:1,0 -f=C:ss -s=reorder(k,i,j)"

  # "A(i,j)=B(i,k)*E(k,l)*F(l,j)+d(i) -f=A:ss:0,1 -f=B:ss:0,1 -f=E:ss:1,0 -f=F:ss:1,0 -f=d:s -s=reorder(i,j)" #reorder: jikl 

  # "A(i,j)=E(i,l)*F(l,k)*C(k,j)+d(i) -f=A:ss:0,1 -f=E:ss:0,1 -f=F:ss:1,0 -f=C:ss:1,0 -f=d:s -s=reorder(i,j)" #reorder: jikl 
  # "A(j,k)=E(j,i)*F(i,l)*C(l,k)+d(j) -f=A:ss:0,1 -f=E:ss:0,1 -f=F:ss:1,0 -f=C:ss:1,0 -f=d:s -s=reorder(j,k)" #reorder: jikl 
  # "X(j,k)=A(j,k)+d(j) -f=X:ss:0,1 -f=A:ss:0,1 -f=d:s -s=reorder(j,k)" #reorder: jikl 

  # "X(i,j,k,l)=Q(i,k,j,m)*K(i,l,j,m) -f=X:ssss:0,1,2,3 -f=B:ssss:0,2,1,3 -f=C:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"
#   "X(i,j,k)=B(j,l)*C(i,l,k) -f=X:sss:0,2,1 -f=B:ss:1,0 -f=C:sss:0,2,1" #reorder: jikl 
#   "X(i,j,k)=C(i,l,k)+D(j) -f=X:sss:0,2,1 -f=B:ss:1,0 -f=C:sss:0,2,1 -s=reorder(i,k,l,j)" #reorder: jikl 
  # "X(i,k,j,m)=B(i,j,k,l)*C(i,l,j,m) -f=X:ssss:0,1,2,3 -f=B:ssss:0,2,1,3 -f=C:ssss:0,3,1,2 -s=reorder(i,k,j,m,l)"
  # "X(i,k,j,m)=B(i,j,k,l)*C(i,l,j,m) -f=X:ssss:0,2,1,3 -f=B:ssss:0,1,2,3 -f=C:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"
  # "X(i,k,j,m)=Q(i,k,j,m)*K(i,l,j,m)*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,2,1,3 -f=V:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"
  #"X(i,j,k,l)=Q(i,k,j,m)*K(i,l,j,m) -f=X:ssss:0,1,2,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"

  #"X(i,j)=B(i,k)*C(k,j) -f=X:ss -f=B:ss -f=C:ss:1,0  -s=reorder(i,j,k)"

  # "X(i,j)=B(i,j)*C(i,k)*D(k,j) -f=X:ss -f=B:ss -f=C:dd -f=D:dd:1,0 -s=reorder(i,j,k)"

  # "X(i,k,j,m)=B(i,j,k,l)*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=B:ssss:0,1,2,3 -f=V:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"
  # "X(i,k,j,m)=B(i,j,k,l)*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=B:ssss:0,1,2,3 -f=V:ssss:0,2,3,1 -s=reorder(i,j,k,m,l)"
  # "X(i,k,j,m)=B(i,j,k,l)*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=B:ssss:0,1,3,2 -f=V:ssss:0,2,1,3 -s=reorder(j,i,l,k,m)"
  #"X(i,k,j,m)=B(i,j,k,l)*V(i,l,j,m) -f=X:ssss:0,2,3,1 -f=B:ssss:0,1,3,2 -f=V:ssss:0,2,1,3 -s=reorder(i,j,l,m,k)"
  #"X(i,k,j,m)=B(i,j,k,l)*V(i,l,j,m) -f=X:ssss:2,0,3,1 -f=B:ssss:1,0,3,2 -f=V:ssss:2,0,3,1 -s=reorder(j,i,m,l,k)"
  # "X(i,k,j,m)=(Q(i,k,j,m)*K(i,l,j,m))*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,2,1,3 -f=V:ssss:0,2,1,3 -s=reorder(i,j,k,l,m)"
   # "X(i,k,j,m)=(Q(i,k,j,m)*K(i,l,j,m))*V(i,l,j,m) -f=X:ssss:0,2,1,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,2,1,3 -f=V:ssss:0,2,1,3 -s=reorder(i,j,k,m,l)"
#   "X(i,k,j,m)=Q(i,k,j,m)*K(i,l,j,m) -f=X:ssss:0,1,2,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,3,1,2 -s=reorder(i,k,j,m,l)"
  # "X(i,k,j,n)=(Q(i,k,j,m)*K(i,l,j,m))*V(i,l,j,n) -f=X:ssss:0,2,1,3 -f=Q:ssss:0,2,1,3 -f=K:ssss:0,2,1,3 -f=V:ssss:0,2,1,3 -s=reorder(i,j,k,l,m,n)"
  # "X(i,k,j,m)=(Q(i,k,j,m)*K(i,l,j,m))*V(i,l,j,m)"
  # "X(i,j)=B(i,j)+C(j) -f=B:ss -f=C:s"
)

mkdir -p $dir
mkdir -p $dot_dir
mkdir -p $png_dir

for i in ${!KERNEL_NAMES[@]}; do
    name=${KERNEL_NAMES[$i]}
    args=${TACO_ARGS[$i]}

    $taco_exe $args --print-sam-graph="$name.pbtxt"
    #dot -Tpng $name.pbtxt -o $name.png
    echo "Generating sam for $name to $dir"
done

