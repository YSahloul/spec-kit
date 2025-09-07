#!/bin/bash
# Setup script for spec-kit configuration

set -e

echo "Setting up spec-kit configuration..."

# Create global config directory
GLOBAL_CONFIG_DIR="$HOME/.config/opencode/spec-kit"
echo "Creating global config directory: $GLOBAL_CONFIG_DIR"
mkdir -p "$GLOBAL_CONFIG_DIR"

# Create default global config
GLOBAL_CONFIG_FILE="$GLOBAL_CONFIG_DIR/config.json"
if [ ! -f "$GLOBAL_CONFIG_FILE" ]; then
    echo "Creating default global configuration..."
    cat > "$GLOBAL_CONFIG_FILE" << 'EOF'
{
  "version": "1.0.0",
  "theme": "auto",
  "auto_save": true,
  "keyboard_shortcuts": {
    "/spec": "ctrl+s",
    "/plan": "ctrl+p",
    "/tasks": "ctrl+t",
    "/research": "ctrl+r",
    "/analyze": "ctrl+a",
    "/migrate": "ctrl+m"
  },
  "extensions": {
    "spec-kit": true,
    "git-integration": true,
    "research-engine": true
  },
  "workspace_settings": {
    "default_template": "default",
    "max_concurrent_tasks": 3,
    "auto_commit": true
  },
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
EOF
    echo "✓ Global config created at $GLOBAL_CONFIG_FILE"
else
    echo "✓ Global config already exists at $GLOBAL_CONFIG_FILE"
fi

# Create state file
STATE_FILE="$GLOBAL_CONFIG_DIR/state.json"
if [ ! -f "$STATE_FILE" ]; then
    echo "Creating state tracking file..."
    cat > "$STATE_FILE" << 'EOF'
{
  "version": "1.0.0",
  "last_updated": "2024-01-01T00:00:00",
  "projects": {},
  "global_stats": {
    "total_specs_created": 0,
    "total_plans_created": 0,
    "total_tasks_generated": 0,
    "total_research_items": 0
  }
}
EOF
    echo "✓ State file created at $STATE_FILE"
else
    echo "✓ State file already exists at $STATE_FILE"
fi

# Check if --project flag is provided
if [ "$1" = "--project" ]; then
    echo "Setting up project-specific configuration..."

    # Get current directory as project path
    PROJECT_PATH="$(pwd)"
    PROJECT_CONFIG_DIR="$PROJECT_PATH/.opencode/spec-kit"

    echo "Creating project config directory: $PROJECT_CONFIG_DIR"
    mkdir -p "$PROJECT_CONFIG_DIR"

    # Create project config
    PROJECT_CONFIG_FILE="$PROJECT_CONFIG_DIR/config.json"
    if [ ! -f "$PROJECT_CONFIG_FILE" ]; then
        echo "Creating project configuration..."
        # Use current timestamp
        CREATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        UPDATED_AT=$CREATED_AT

        # Create config with project path
        cat > "$PROJECT_CONFIG_FILE" << EOF
{
  "project_path": "$PROJECT_PATH",
  "spec_kit_enabled": true,
  "default_template": "default",
  "auto_commit": true,
  "git_integration": true,
  "research_enabled": true,
  "custom_settings": {
    "max_tasks_per_spec": 10,
    "default_research_depth": 3,
    "auto_save_interval": 30,
    "backup_enabled": true
  },
  "created_at": "$CREATED_AT",
  "updated_at": "$UPDATED_AT"
}
EOF
        echo "✓ Project config created at $PROJECT_CONFIG_FILE"
    else
        echo "✓ Project config already exists at $PROJECT_CONFIG_FILE"
    fi

    echo "✓ Project configuration setup complete!"
    echo ""
    echo "Project configuration files:"
    echo "  Project config: $PROJECT_CONFIG_FILE"
    exit 0
fi

echo "✓ Spec-kit configuration setup complete!"
echo ""
echo "Configuration files:"
echo "  Global config: $GLOBAL_CONFIG_FILE"
echo "  State file:    $STATE_FILE"
echo ""
echo "To set up project-specific configuration, run this script from your project directory:"
echo "  ./setup-config.sh --project"