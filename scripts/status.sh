#!/bin/bash
echo "=== HODLXXI OAuth Status ==="
echo "App:     $(systemctl is-active app)"
echo "Redis:   $(systemctl is-active redis-server)"
echo "Clients: $(redis-cli SCARD clients:all)"
echo "Memory:  $(redis-cli INFO memory | grep used_memory_human | cut -d: -f2)"
echo ""
echo "Recent errors:"
sudo journalctl -u app --since "1 hour ago" | grep -i error | tail -3
