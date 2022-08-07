
import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Repl mode
        import repl
        repl.main()
    else:
        import runner
        runner.main(sys.argv[1])


