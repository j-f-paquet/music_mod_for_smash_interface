# This script:
# 1) takes input parameters for the initial condition ansatz Trento
# 2) writes an config file for Trento
# 3) runs Trento
# 4) converts the Trento output file in a format that can be read as initial conditions by KoMPoST
# 5) write an input file for KoMPoST that can then be run

import configparser
import os.path
import subprocess
import sys
import shutil

##################################################################
################### 1) Trento input parameters ###################
##################################################################

# Grid used to save Trento and also used later to run KoMPoST
# Total number of grid cell
grid_size=300
# Grid step in fermi
dx=0.08

# Type of ion (Au, Pb, ...)
trento_nucleus='Au'

# Python dictionary containing Trento parameters
trento_parameters = {
'normalization':13.,
'reduced-thickness':0.1,
'fluctuation':0.9,
'nucleon-min-dist':0.4,
'cross-section':4.2, # in fermi
'nucleon-width':0.8,
'b-min':5,
'b-max':5.01,
'random-seed':1
}


##################################################################
################## 2) Writing Trento config file ##################
##################################################################

trento_config_file="trento_config"

if (os.path.isfile(trento_config_file)):
        print("I'd rather not overwrite an existing file (\""+trento_config_file+"\")...  Aborting")
        exit(1)

trento_tmp_dir=trento_nucleus+trento_nucleus

with open(trento_config_file, 'w') as trento_config:
    trento_config.write('projectile = '+trento_nucleus+'\n')
    trento_config.write('projectile = '+trento_nucleus+'\n')
    trento_config.write('number-events = 1\n')
    trento_config.write('output = '+trento_tmp_dir+'\n')
    trento_config.write('grid-max = '+str(grid_size*dx/2.)+'\n')
    trento_config.write('grid-step = '+str(dx)+'\n')
    for param, value in trento_parameters.items():
            trento_config.write(param+' = '+str(value)+'\n')


##################################################################
####################### 3) Running Trento ########################
##################################################################

# Location of Trento executable
trento_bin='trento/trento'

# Run Trento
# subprocess.run(args, *, stdin=None, input=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None)
#print(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),trento_config_file))
#subprocess.Popen([trento_bin, "-c",os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),trento_config_file)], shell=True)
print("event_number impact_param npart mult e2 e3 e4 e5")
os.system(trento_bin+" -c "+os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),trento_config_file))


#shutil.move(os.path.join(trento_tmp_dir,"0.dat"),"trento_raw_output.dat")

##################################################################
############### 4) Trento output to MUSIC intput ###############
##################################################################


kompost_init_name="trento_initial_condition_in_music_format.txt"

if (os.path.isfile(kompost_init_name)):
        print("I'd rather not overwrite an existing file (\""+kompost_init_name+"\")...  Aborting")
        exit(1)

#
# Write header

#        profile >> dummy >> dummy >> dummy2
#                        >> dummy >> neta >> dummy >> nx >> dummy >> ny
#                                        >> dummy >> deta >> dummy >> dx >> dummy >> dy;
#  header << "# tau_in_fm " << tau_in_fm << " etamax= 1 xmax= " << Nx << " ymax= " << Ny << " deta= 0 dx= " << dx << " dy= " << dy << "\n";
header_bash_command="echo '# dummy 0.0 etamax= 1 xmax= "+str(grid_size)+" ymax= "+str(grid_size)+" deta= 10. dx= "+str(dx)+" dy= "+str(dx)+"' > "+kompost_init_name

subprocess.run(header_bash_command, shell=True)

# Use Soeren's bash script, which we know works
#conversion_bash_command="Ns=\""+str(grid_size)+"\"; tail -n+9 "+os.path.join(trento_tmp_dir,"0.dat") +" | perl -pe 's/\s+/\\n/g' | awk -v Ns=${Ns} 'BEGIN {for(x=0;x<Ns;x++){for(y=0;y<Ns;y++){T00[x+Ns*y]=0.0;}} Index=0;} {T00[Index]=$1; Index++;} END {for(y=0;y<Ns;y++){for(x=0;x<Ns;x++){print x,y,T00[x+Ns*y],0.5*T00[x+Ns*y],0.5*T00[x+Ns*y],0.0,0.0,0.0,0.0,0.0,0.0,0.0;} printf(\"\\n\"); }}' > "+kompost_init_name
conversion_bash_command="Ns=\""+str(grid_size)+"\"; tail -n+9 "+os.path.join(trento_tmp_dir,"0.dat") +" | perl -pe 's/\s+/\\n/g' | awk -v Ns=${Ns} 'BEGIN {for(x=0;x<Ns;x++){for(y=0;y<Ns;y++){T00[x+Ns*y]=0.0;}} Index=0;} {T00[Index]=$1; Index++;} END {for(x=0;x<Ns;x++){for(y=0;y<Ns;y++){print 0, (x-"+str(grid_size/2.)+")*"+str(dx)+","+"(y-"+str(grid_size/2.)+")*"+str(dx)+",T00[x+Ns*y],1,0,0,0, 0,0,0,0,0,0,0,0,0,0;} }}' >> "+kompost_init_name

#What MUSIC format???
#
#            ss >> dummy1 >> dummy2 >> dummy3
#                           >> density >> utau >> ux >> uy >> ueta
#                                          >> pitautau >> pitaux >> pitauy >> pitaueta
#                                                         >> pixx >> pixy >> pixeta >> piyy >> piyeta >> pietaeta;


#print(conversion_bash_command)

subprocess.run(conversion_bash_command, shell=True)


##################################################################
################## 5) Writing MUSIC input file #################
##################################################################

setup_file_template="music_input_example"

setup_file_updated="music_input_trento"

box_size=grid_size*dx

#print("sed -e 's/X_grid_size_in_fm [0-9\.]*(\s+.*)$/X_grid_size_in_fm "+str(box_size)+"/g' "+setup_file_template+" > "+setup_file_updated)

subprocess.run("sed -e 's/^X_grid_size_in_fm .*$/X_grid_size_in_fm "+str(box_size)+"/g' "+setup_file_template+" > "+setup_file_updated, shell=True)
subprocess.run("sed -i -e 's/^Y_grid_size_in_fm .*$/Y_grid_size_in_fm "+str(box_size)+"/g' "+setup_file_updated, shell=True)

subprocess.run("sed -i -e 's/^Grid_size_in_x .*$/Grid_size_in_x "+str(grid_size)+"/g' "+setup_file_updated, shell=True)
subprocess.run("sed -i -e 's/^Grid_size_in_y .*$/Grid_size_in_y "+str(grid_size)+"/g' "+setup_file_updated, shell=True)

subprocess.run("sed -i -e 's/^Initial_Distribution_input_filename .*$/Initial_Distribution_input_filename "+kompost_init_name+"/g' "+setup_file_updated, shell=True)

#X_grid_size_in_fm 20.0        # spatial range along x direction in the
## transverse plane
## [-X_grid_size_in_fm/2, X_grid_size_in_fm/2]
#Y_grid_size_in_fm 20.0        # spatial range along y direction in the
## transverse plane
## [-Y_grid_size_in_fm/2, Y_grid_size_in_fm/2]
#Grid_size_in_y 200            # number of the grid points in y direction
#Grid_size_in_x 200            # number of the grid points in x direction
