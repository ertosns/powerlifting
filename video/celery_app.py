"""
Celery application and video processing task.
"""
import os
import json
import logging
from datetime import datetime

from celery import Celery

logger = logging.getLogger(__name__)

# Celery configuration
BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery = Celery('powerlifting_video', broker=BROKER_URL, backend=RESULT_BACKEND)
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,      # 30 min max per video
    task_soft_time_limit=1500,  # 25 min soft limit
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks (memory management)
)


@celery.task(bind=True, name='process_video_task')
def process_video_task(self, job_id: int):
    """
    Celery task to process a video job.
    Reads VideoJob from DB, runs the processor, updates status.
    """
    from models import app, db
    from models import VideoJob, Record, User
    from video.processor import VideoConfig, RepTimestamp, process_video
    from powerlifting import wilks_score, get_total, compute_analysis

    with app.app_context():
        job = VideoJob.query.get(job_id)
        if not job:
            logger.error(f"VideoJob {job_id} not found")
            return {'status': 'failed', 'error': 'Job not found'}

        try:
            # Update status to processing
            job.status = 'processing'
            db.session.commit()
            self.update_state(state='PROCESSING', meta={'job_id': job_id})

            # Parse rep timestamps
            timestamps_raw = json.loads(job.rep_timestamps_json)
            rep_timestamps = [
                RepTimestamp(start_sec=t['start_sec'], end_sec=t['end_sec'])
                for t in timestamps_raw
            ]

            # Gather user's lift history for the progression chart
            records = Record.query.filter_by(user_id=job.user_id).order_by(Record.id).all()
            history_data = _build_history_data(records)

            # Compute Wilks and analysis from the latest record or current data
            wilks = 0.0
            analysis = ""
            if records:
                last = records[-1]
                row = {
                    'deadlift': last.deadlift,
                    'squat': last.squat,
                    'bench': last.bench,
                    'weight': last.weight,
                    'gender': last.gender,
                }
                wilks = wilks_score(row)
                analysis = compute_analysis(last)

            # Build processing config
            input_path = os.path.join('data', 'uploads', job.input_filename)
            output_filename = f"processed_{job.id}_{job.theme_name}.mp4"
            output_path = os.path.join('data', 'outputs', output_filename)

            config = VideoConfig(
                input_path=input_path,
                output_path=output_path,
                lift_type=job.lift_type,
                weight_kg=job.weight_kg,
                total_reps=job.total_reps,
                rep_timestamps=rep_timestamps,
                theme_name=job.theme_name,
                audio_mode=job.audio_mode,
                is_pr=job.is_pr,
                wilks_score=wilks,
                analysis_text=analysis,
                history_data=history_data,
            )

            # Process the video
            result_path = process_video(config)

            # Update job as complete
            job.status = 'complete'
            job.output_filename = output_filename
            job.completed_at = datetime.utcnow().isoformat()
            db.session.commit()

            logger.info(f"Job {job_id} completed: {result_path}")
            return {'status': 'complete', 'output': output_filename}

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)[:500]
            db.session.commit()
            return {'status': 'failed', 'error': str(e)[:200]}


def _build_history_data(records) -> dict:
    """Build history dict from user's records for the progression chart overlay."""
    if not records:
        return {}

    dates = []
    totals = []
    squats = []
    benches = []
    deadlifts = []

    for r in records:
        if r.is_target == 'target':
            continue
        dates.append(r.datetime)
        squats.append(r.squat)
        benches.append(r.bench)
        deadlifts.append(r.deadlift)
        totals.append(r.squat + r.bench + r.deadlift)

    if not dates:
        return {}

    return {
        'dates': dates,
        'totals': totals,
        'squats': squats,
        'benches': benches,
        'deadlifts': deadlifts,
    }
