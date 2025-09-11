# 2. Your first project

DishPy makes it easy to create a new VEX V5 Python project with the proper structure and files.

## Creating Your First Project

To create a new project, use the `create` command:

```bash
uvx dishpy create --name "my-robot"
```

You can also specify which slot on the V5 brain your program should use (defaults to slot 1):

```bash
uvx dishpy create --name "my-robot" --slot 2
```

### Using a Template

DishPy supports project templates to help you get started with different robot configurations or code patterns. Use the `--template` option to select a template when creating your project:

```bash
uvx dishpy create --name "my-robot" --template TEMPLATE_NAME
```

Available templates:
- right_arcade_control
- clawbot_controller_tank
- clawbot
- empty
- limit_bumper_sensing
- drive_to_location_gps
- using_threads
- competition_template
- split_arcade_control
- drivetrain_sensing

For example, to start a project with the `clawbot` template:

```bash
uvx dishpy create --name "my-robot" --template clawbot
```

## Project Structure

After running the create command, DishPy will generate a project directory with the following structure:

```
my-robot/
├── dishpy.toml          # Project configuration file
├── src/                 # Source code directory
│   ├── main.py         # Your main robot code
│   └── vex/            # VEX Python API
│       └── __init__.py # VEX library stubs for development
└── .out/               # Build output directory
```

### File Explanations

- **`dishpy.toml`**: Configuration file containing your project name and V5 brain slot number
- **`src/main.py`**: Your main robot program - this is where you'll write your code
- **`src/vex/__init__.py`**: VEX Python API stubs that provide code completion and type hints in your editor
- **`.out/`**: Directory where DishPy places the final combined code before uploading to the brain

## Building and Uploading Your Project

### 1. Write Your Code

First, let's add some basic code to see our robot in action. Open `src/main.py` and replace the template with:

```python
import vex

# Create a brain instance to access the V5 brain
brain = vex.Brain()

# Print a message to the brain's screen
brain.screen.print("Hello from DishPy!")
brain.screen.next_row()
brain.screen.print("My robot is running!")
```

### 2. Connect Your V5 Brain

Make sure your VEX V5 brain is connected to your computer via USB cable and is powered on.

### 3. Upload to Brain

Now you can build and upload your project to the V5 brain:

```bash
uvx dishpy mu
```

The `mu` command will:
1. Combine all your project files into a single Python file
2. Place the combined code in `.out/main.py`
3. Upload the program to your V5 brain

> **Note**: Since this is a simple single-file project, the `.out/main.py` file will be nearly identical to your `src/main.py`. The real power of DishPy's code combination becomes apparent when you start using multiple files and importing local modules, which we'll cover in later tutorials.

After uploading and running, you should see your message displayed on the V5 brain's screen!

## Opening a Terminal to the V5 Brain

DishPy also provides a convenient way to open a terminal connection to your V5 brain for debugging and monitoring:

```bash
uvx dishpy terminal
```

This command opens a direct terminal connection to the V5 brain, allowing you to see print output from your program in real-time and interact with the brain's console. This is especially useful for debugging your robot programs.
