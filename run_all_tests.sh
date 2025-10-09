#!/bin/bash
# Master Test Runner for AI Video Automation Pipeline

echo "🧪 AI VIDEO AUTOMATION PIPELINE - COMPREHENSIVE TESTING SUITE 🧪"
echo
echo "Available tests:"
echo "================"
echo
echo "1. 🚀 Start API Server       - test_1_start_api.sh"
echo "2. 🗄️  Database Operations    - python test_2_database.py"
echo "3. 🎬 Video Pipeline         - python test_3_video_pipeline.py"
echo "4. 🔗 API Endpoints          - python test_4_api_endpoints.py"
echo "5. ⚡ Task Queue System      - python test_5_task_queue.py"
echo "6. 🚀 Full Integration       - python test_6_full_integration.py"
echo
echo "Quick tests (automated):"
echo "========================"
echo "7. 🔥 Run all tests (2-6)   - ./run_all_tests.sh auto"
echo
echo "Interactive mode:"
echo "================"

while true; do
    echo
    read -p "Enter test number (1-7) or 'q' to quit: " choice
    
    case $choice in
        1)
            echo "Starting API server..."
            ./test_1_start_api.sh
            ;;
        2)
            echo "Running database test..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate && python test_2_database.py
            ;;
        3)
            echo "Running video pipeline test..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate && python test_3_video_pipeline.py
            ;;
        4)
            echo "Running API endpoints test..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate && python test_4_api_endpoints.py
            ;;
        5)
            echo "Running task queue test..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate && python test_5_task_queue.py
            ;;
        6)
            echo "Running full integration test..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate && python test_6_full_integration.py
            ;;
        7|auto)
            echo "Running all automated tests..."
            cd /home/labber/AI_VOICE_AUTOMATION && source venv/bin/activate
            
            echo
            echo "🗄️  TEST 2: Database Operations"
            echo "================================"
            python test_2_database.py
            
            echo
            echo "🎬 TEST 3: Video Pipeline"
            echo "========================="
            python test_3_video_pipeline.py
            
            echo
            echo "🔗 TEST 4: API Endpoints"
            echo "======================="
            python test_4_api_endpoints.py
            
            echo
            echo "⚡ TEST 5: Task Queue System"
            echo "==========================="
            python test_5_task_queue.py
            
            echo
            echo "🚀 TEST 6: Full Integration"
            echo "=========================="
            python test_6_full_integration.py
            
            echo
            echo "🎉 ALL TESTS COMPLETED!"
            if [ "$choice" = "auto" ]; then
                break
            fi
            ;;
        q|Q|quit|exit)
            echo "Goodbye!"
            break
            ;;
        *)
            echo "Invalid choice. Please enter 1-7 or 'q' to quit."
            ;;
    esac
done