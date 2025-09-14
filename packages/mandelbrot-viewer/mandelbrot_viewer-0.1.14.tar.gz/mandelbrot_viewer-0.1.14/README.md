# mandelbrot-set-viewer
An interactive arbitrary precision Mandelbrot set viewer using my [taichi_big_float](https://github.com/balazs-szalai/taichi-bigfloat) package.

## Usage
You just have to install it using pip:
	
	pip install mandelbrot-viewer
And you can run it from the commandline using:
	
	mandelbrot-viewer
This will execute the main function from mandelbrot_viewer.mandelbrot_viewer.py. 
There are a few arguments you can give, they have strict ordering. The first you can set 'server' or anything else.
If set to 'server', this setting expexts to be able to connect to an already running server, launched by the remote_ssh_server.py which can be launched as 
	
	mandelbrot-remote-server
This solution was implemented in order to be able to run the heavy part of the computation on any SSH HPC which allows port forwarding from the compute node. To use this you first need to set up portforwarding through SSH on the port 6010 on the HPC server compute node you are using and then launch the mandelbrot-remote-server on it. Then you should be able to connect to this server with setting the first argument of the mandelbrot viewer to 'server' as

	mandelbrot-viewer server
You can also provide a second parameter (necessarily in this order), which is either 'cuda' or anything else. If it is set to 'cuda' it tries to launch the computations on the cuda platform, otherwise it starts it on cpu. This is not recommended since the default is to try to use cuda and if it fails it will automatically fall back to cpu.
But it can be used as
	
	mandelbrot-viewer local cpu
This starts the viewer locally only using the cpu.

## Notes
The arbitrary precision calculations are solved in a way that the functions and the Taichi kernels are dynamically created and compiled for higher and higher precisions, this compilation might takes some time, this does not block the GUI, but if the kernel isn't yet compiled for the necessary precision, you can see the result being pixelated, in this case you have to be a bit patient and wait for the kernels to compile (there is not yet a signal implemented for this, so it does not trigger a recompute, you have to poke the GUI to see if it is still pixelated or not).