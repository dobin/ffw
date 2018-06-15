all: vulnserver_plain_asan vulnserver_plain vulnserver_hfuzz

vulnserver_plain:
	gcc -g -O0 -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain

vulnserver_plain_asan:
	gcc -g -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain_asan

vulnserver_hfuzz:
	/Development/honggfuzz/hfuzz_cc/hfuzz-clang -g -O0 vulnserver.c -o vulnserver_hfuzz

clean:
	rm vulnserver_plain_asan vulnserver_plain vulnserver_hfuzz
