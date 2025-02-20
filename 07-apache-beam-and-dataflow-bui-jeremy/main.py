import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, WorkerOptions
from apache_beam.io import fileio
import time

class ExtractLinksFn(beam.DoFn):
    def process(self, file):
        page_name = file.metadata.path.split('/')[-1].split('.')[0]
        page_content = file.read_utf8().splitlines()
        outgoing_links = [
            line.split('"')[1].split('.')[0]
            for line in page_content
            if 'href' in line.lower() and '"' in line
        ]
        yield (page_name, outgoing_links)

class ComputeLinkStatistics(beam.DoFn):
    def process(self, element):
        page, links = element
        yield (page, len(links))

def run_pipeline():
    bucket_name = 'jeremybui_ps2'
    folder_name = 'files'

    job_name = f"apache-beam-dataflow-job-{int(time.time())}"

    # Set up PipelineOptions with DataflowRunner or DirectRunner
    options = PipelineOptions(
        runner='DirectRunner',
        project='ds561-bucs',
        region='us-central1',
        job_name=job_name,
        staging_location=f'gs://{bucket_name}/staging',
        temp_location=f'gs://{bucket_name}/temp',
        requirements_file='requirements.txt'
    )

    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.service_account_email = 'dataflow-service@ds561-bucs.iam.gserviceaccount.com'

    worker_options = options.view_as(WorkerOptions)
    worker_options.num_workers = 4

    start_time = time.time()
    
    with beam.Pipeline(options=options) as p:
        files = (p
                 | "Match Files" >> beam.io.fileio.MatchFiles(f'gs://{bucket_name}/{folder_name}/*')
                 | "Read Matches" >> beam.io.fileio.ReadMatches())

        link_data = (files
                     | "Extract Links" >> beam.ParDo(ExtractLinksFn()))

        outgoing_counts = (link_data
                           | "Compute Outgoing Links" >> beam.ParDo(ComputeLinkStatistics())
                           | "Combine Outgoing to List" >> beam.combiners.ToList()
                           | "Top 5 Outgoing" >> beam.Map(lambda elements: sorted(elements, key=lambda x: x[1], reverse=True)[:5]))

        incoming_counts = (link_data
                           | "Flatten Links" >> beam.FlatMap(lambda x: [(link, 1) for link in x[1]])
                           | "Count Incoming Links" >> beam.combiners.Count.PerKey()
                           | "Combine Incoming to List" >> beam.combiners.ToList()
                           | "Top 5 Incoming" >> beam.Map(lambda elements: sorted(elements, key=lambda x: x[1], reverse=True)[:5]))

        outgoing_counts | "Write Top Outgoing" >> beam.io.WriteToText(f'gs://{bucket_name}/top_outgoing')
        incoming_counts | "Write Top Incoming" >> beam.io.WriteToText(f'gs://{bucket_name}/top_incoming')

    end_time = time.time()
    runtime = end_time - start_time
    print(f"Pipeline runtime: {runtime:.2f} seconds")

if __name__ == "__main__":
    print("Running pipeline...")
    run_pipeline()
