import logging
from celery import shared_task
from .models import ExtractionJob, ExtractedRecord
from connectors.services import get_connector

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_extraction_task(self, job_id, filters=None, order_by=None, order_dir='asc'):
    """
    Celery task that runs a data extraction job in the background.
    Called by the API immediately after creating the job record,
    so the HTTP request returns instantly with status 'pending'.
    """
    try:
        # Get the job
        job = ExtractionJob.objects.select_related('connection').get(id=job_id)

        # Mark as running
        job.status = 'running'
        job.save()

        logger.info(f'Starting extraction job {job_id} for table {job.table_name}')

        # Get the connector and fetch data
        connector = get_connector(job.connection)
        rows = connector.fetch_data(
            table_name=job.table_name,
            batch_size=job.batch_size,
            offset=0,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir,
        )

        # Save all rows in a single DB query
        records_to_create = []
        for row in rows:
            clean_row = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in row.items()
            }
            records_to_create.append(ExtractedRecord(job=job, data=clean_row))
        ExtractedRecord.objects.bulk_create(records_to_create, batch_size=500)

        # Mark as completed
        job.status = 'completed'
        job.save()

        logger.info(f'Extraction job {job_id} completed — {len(records_to_create)} records saved')
        return {'status': 'completed', 'records': len(records_to_create)}

    except ExtractionJob.DoesNotExist:
        logger.error(f'Extraction job {job_id} not found')
        raise

    except Exception as e:
        logger.error(f'Extraction job {job_id} failed: {str(e)}')
        # Mark job as failed
        try:
            job = ExtractionJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
        except Exception:
            pass
        raise