all: clienttest_asan clienttest_plain 

clienttest_asan:
	gcc -g -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer clienttest.c -o clienttest_asan

clienttest_plain:
	gcc -g -O0 -fno-stack-protector -fno-omit-frame-pointer clienttest.c -o clienttest_plain


clean:
	rm clienttest_asan clienttest_plain coverageserver_plain
