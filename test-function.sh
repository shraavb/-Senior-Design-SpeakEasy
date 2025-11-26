#!/bin/bash
curl -X POST 'https://goyhiczyiwsosgyzkboq.supabase.co/functions/v1/language-conversation' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdveWhpY3p5aXdzb3NneXprYm9xIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAxODU3NDYsImV4cCI6MjA3NTc2MTc0Nn0.eDrvYsv5BMtSA4nStnjn0VPb8ScWbtimnxJ4leYtkaI' \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Yo quiero un café"}],"language":"Spanish","scenario":"Ordering","level":"Intermediate","feedbackMode":"on","provideFeedback":true}'
