# functions to manipulate xyz files:

# The awk format to use for xyz lines:
XYZFORMAT="%3s  %14f  %14f  %14f"

rotate_axis_to_z() {
	# rotate the molecule given by an xyz file such that the axis
	# given as $1 is the new z axis. 
	# reads the molecule on stdin
	# $1: axis which should be rotated to z

	case "$1" in
		z)
			# nothing to do
			cat
			;;

		x|y)  : All fine
			;;
		*)
			echo "rotate_axis_to_z expects an orientation (x,y or z) as first arg, not $1" >&2
			return 1
			;;
	esac

	awk -v "axis=$1" -v "xyzformat=$XYZFORMAT" '
		# cat first two lines
		NR==1 || NR==2 { print; next }

		# others: do rotation
		axis == "x" {
			# x->z, y->x, z->y
			printf xyzformat "\n", $1, $3, $4, $2
		}

		axis == "y" {
			# y->z, z->x, x->y
			printf xyzformat "\n", $1, $4, $2, $3
		}
	'
}

build_dimer() {
	# build a dimer xyz from a monomer xyz we get on stdin
	# $1: orientation: x,y,z --> direction in which separation should be applied
	# $2: distance in Å      --> how much should monomers be separated

	case "$1" in
		x|y|z)  : All fine
			;;
		*)
			echo "build_dimer expects an orientation (x,y or z) as first arg, not $1" >&2
			return 1
			;;
	esac

	if [ -z "$2" ]; then
		echo "build_dimer expects a separation as first arg, not $2" >&2
		return 1
	fi

	awk -v "dist=$2" -v "orient=$1" -v "xyzformat=$XYZFORMAT" '
		BEGIN {
			halfdist=dist/2
		}

		NR==1 {
			# we now have twice as many atoms:
			print 2*$0
			next
		}

		NR==2 {
			# copy comment line:
			print
			next
		}

		# all other lines:
		orient == "x" {
			printf xyzformat "\n", $1, $2-halfdist, $3, $4
			printf xyzformat "\n", $1, $2+halfdist, $3, $4
		}
		orient == "y" {
			printf xyzformat "\n", $1, $2, $3-halfdist, $4
			printf xyzformat "\n", $1, $2, $3+halfdist, $4
		}
		orient == "z" {
			printf xyzformat "\n", $1, $2, $3, $4-halfdist
			printf xyzformat "\n", $1, $2, $3, $4+halfdist
		}
	'
}
