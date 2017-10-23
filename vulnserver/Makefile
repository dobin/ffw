all: vulnserver_asan vulnserver_plain

vulnserver_asan:
	gcc -g -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_asan

vulnserver_plain:
	gcc -g -O0 -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain

clean:
	rm vulnserver_asan vulnserver_plain
