#!/usr/bin/env python3
"""
Test script to verify all compiler fixes work correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from minecraft_datapack_language.mdl_compiler import MDLCompiler
from minecraft_datapack_language.mdl_parser import MDLParser
from minecraft_datapack_language.mdl_parser import MDLParser

def test_complex_expressions():
    """Test that complex expressions compile correctly."""
    print("Testing complex expressions...")
    
    source = """
pack "test" "Test pack" 82;
namespace "test";

var num counter<@s> = 0;
var num health<@s> = 20;
var num bonus<@s> = 5;

function test:complex_math<@s> {
    counter<@s> = ($counter<@s>$ + $health<@s>$) * $bonus<@s>$;
}
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Parse and compile
        parser = MDLParser("<test>")
        ast = parser.parse(source)
        
        compiler = MDLCompiler(temp_dir)
        compiler.compile(ast)
        
        # Check output
        output_file = Path(temp_dir) / "data" / "test" / "function" / "complex_math.mcfunction"
        assert output_file.exists(), "Output file should exist"
        
        content = output_file.read_text()
        print(f"Generated content:\n{content}")
        
        # Verify it contains valid Minecraft commands
        # Temp variables may be assigned via set or operation depending on operands
        assert ("scoreboard players set @s temp_" in content) or ("scoreboard players operation @s temp_" in content), "Should generate temporary variable assignment"
        # Add operations may use "+=" with another score; accept either form
        assert ("scoreboard players add @s temp_" in content) or ("+= @s" in content), "Should generate add operations"
        assert "scoreboard players operation @s temp_" in content, "Should generate scoreboard operations"
        
        print("✅ Complex expressions test passed!")

def test_control_flow():
    """Test that control flow structures compile correctly."""
    print("Testing control flow...")
    
    source = """
pack "test" "Test pack" 82;
namespace "test";

var num counter<@s> = 0;

function test:control_test<@s> {
    if $counter<@s>$ > 5 {
        say "High counter!";
    } else if $counter<@s>$ > 2 {
        say "Medium counter!";
    } else {
        say "Low counter!";
    }
    
    while $counter<@s>$ < 10 {
        counter<@s> = $counter<@s>$ + 1;
        $!raw
          say   Hello
        raw!$
    }
}
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Parse and compile
        parser = MDLParser()
        ast = parser.parse(source)
        
        compiler = MDLCompiler(temp_dir)
        compiler.compile(ast)
        
        # Check output
        output_file = Path(temp_dir) / "data" / "test" / "function" / "control_test.mcfunction"
        assert output_file.exists(), "Output file should exist"

        content = output_file.read_text()
        print(f"Generated content:\n{content}")

        # Verify it contains proper control flow
        assert "execute if score" in content, "Should generate execute if commands"
        assert "execute unless score" in content, "Should generate execute unless commands"
        # While body is emitted as a generated function call with parent-name prefix
        assert "__while_" in content, "Should generate while loop functions"
        # Raw block lines should be trimmed per line within generated function files
        mcfuncs = list((Path(temp_dir) / "data" / "test").rglob("*.mcfunction"))
        combined = "\n".join(p.read_text() for p in mcfuncs)
        assert "\nsay   Hello" in combined
        assert "\n  say" not in combined
        
        print("✅ Control flow test passed!")

def test_function_execution():
    """Test that function execution works correctly."""
    print("Testing function execution...")
    
    source = """
pack "test" "Test pack" 82;
namespace "test";

function test:helper<@s> {
    say "Helper function!";
}

function test:main<@s> {
    exec test:helper;
    exec test:helper<@s>;
    exec test:helper<@a>;
}
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Parse and compile
        parser = MDLParser()
        ast = parser.parse(source)
        
        compiler = MDLCompiler(temp_dir)
        compiler.compile(ast)
        
        # Check output
        main_file = Path(temp_dir) / "data" / "test" / "function" / "main.mcfunction"
        assert main_file.exists(), "Main function file should exist"
        
        content = main_file.read_text()
        print(f"Generated content:\n{content}")
        
        # Verify function calls
        assert "function test:helper" in content, "Should generate function call without scope"
        assert "execute as @s run function test:helper" in content, "Should generate function call with @s scope"
        assert "execute as @a run function test:helper" in content, "Should generate function call with @a scope"
        
        print("✅ Function execution test passed!")

def test_variable_scopes():
    """Test that variable scopes are handled correctly."""
    print("Testing variable scopes...")
    
    source = """
pack "test" "Test pack" 82;
namespace "test";

var num global_score<@a> = 0;
var num player_score<@s> = 100;

function test:scope_test<@s> {
    global_score<@a> = $player_score<@s>$;
    player_score<@s> = ($global_score<@a>$ + 10) * 2;
}
"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Parse and compile
        parser = MDLParser()
        ast = parser.parse(source)
        
        compiler = MDLCompiler(temp_dir)
        compiler.compile(ast)
        
        # Check output
        output_file = Path(temp_dir) / "data" / "test" / "function" / "scope_test.mcfunction"
        assert output_file.exists(), "Output file should exist"
        
        content = output_file.read_text()
        print(f"Generated content:\n{content}")
        
        # Verify scope handling
        # Copy from another score should use operation, not set with 'score ...'
        assert "scoreboard players operation @a global_score = @s player_score" in content, "Should copy @s->@a via operation"
        # Assignment to player_score uses temp operation then operation set; accept operation form
        assert ("scoreboard players set @s player_score" in content) or ("scoreboard players operation @s player_score =" in content), "Should handle @s scope"
        assert "@s player_score" in content, "Should reference @s player_score somewhere"
        # Read from @a appears in temp operations; accept either explicit read or operation form
        assert ("score @a global_score" in content) or ("= @a global_score" in content)
        
        print("✅ Variable scopes test passed!")

def main():
    """Run all tests."""
    print("Running compiler fix tests...\n")
    
    try:
        test_complex_expressions()
        test_control_flow()
        test_function_execution()
        test_variable_scopes()
        
        print("\n🎉 All tests passed! The compiler fixes are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
