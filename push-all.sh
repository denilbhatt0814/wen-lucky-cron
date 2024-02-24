echo "Starting rebuild..."
docker-compose build

echo "RE-TAGGING IMAGES"
docker tag cron-test-celery_worker denilbhatt0814/cron-test-celery_worker
docker tag cron-test-celery_beat denilbhatt0814/cron-test-celery_beat
docker tag cron-test-celery_flower denilbhatt0814/cron-test-celery_flower
docker tag cron-test-participation_service denilbhatt0814/cron-test-participation_service

echo "PUSHING TO DOCKER HUB..."
docker push denilbhatt0814/cron-test-celery_worker
docker push denilbhatt0814/cron-test-celery_beat
docker push denilbhatt0814/cron-test-celery_flower
docker push denilbhatt0814/cron-test-participation_service
echo "COMPLETE!!"