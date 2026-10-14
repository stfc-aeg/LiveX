import type {
  InferencingEndpointResultTypes,
  InferencingEndpointTypes,
  InferencingLineResult,
} from '../../EndpointTypes';

import { Row, Col, Form, FloatingLabel } from 'react-bootstrap';
import { type AdapterEndpoint, useAdapterEndpoint, WithEndpoint, TitleCard } from '@dssg/odin-react';
import { useEffect, useRef, useState } from 'react';

import MonitorGraph from '../furnace/MonitorGraph';
import { floatingInputStyle, floatingLabelStyle, checkNull, checkNullNoDp } from '../../utils';

interface InferencingCardProps {
  endpoint: AdapterEndpoint<InferencingEndpointTypes>;
  endpoint_url: string;
  name: string;
}

const EndpointSelect = WithEndpoint(Form.Select);

interface BitmapImageProps {
  endpoint_url: string;
  endpoint_name: string;
  graph_name: string;
  alt: string;
}

function BitmapImage({ endpoint_url, endpoint_name, graph_name, alt }: BitmapImageProps) {
  const [src, setSrc] = useState<string>();
  const imageEndpoint = useAdapterEndpoint<InferencingEndpointTypes>(
    'inferencing', endpoint_url, 1000
  );
  const getRef = useRef(imageEndpoint.get);
  getRef.current = imageEndpoint.get;
  const graph = imageEndpoint.data?.endpoint?.[endpoint_name]?.results?.[graph_name];
  const isBitmapGraph = typeof graph !== 'number' && graph?.type === 'bitmap';
  const path = `endpoint/${endpoint_name}/results/${graph_name}/results/_image`;

  useEffect(() => {
    if (!isBitmapGraph) {
      setSrc(undefined);
      return;
    }

    let active = true;
    let requestPending = false;
    let objectUrl: string | undefined;

    const updateImage = async () => {
      if (requestPending) return;
      requestPending = true;
      try {
        const image = await getRef.current<Blob>(path, { responseType: 'blob' });
        if (!active || image.size === 0) return;

        const nextUrl = URL.createObjectURL(image);
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = nextUrl;
        setSrc(nextUrl);
      } catch {
        return;
      } finally {
        requestPending = false;
      }
    };

    void updateImage();
    const intervalId = window.setInterval(() => void updateImage(), 1000);
    return () => {
      active = false;
      window.clearInterval(intervalId);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [isBitmapGraph, path]);

  return src ? (
    <img src={src} alt={alt} style={{ maxWidth: '100%', maxHeight: '70vh' }} />
  ) : (
    <div role="status">Waiting for image.</div>
  );
}

type InferenceGraph = {
  graphId: string;
  graph: InferencingEndpointResultTypes;
  series: Array<[string, InferencingLineResult['results'][string]]>;
};

function InferencingCard(props: InferencingCardProps) {
    const {endpoint, endpoint_url, name} = props;

    const datapath = endpoint?.data?.endpoint?.[name];
    const results = endpoint?.data?.endpoint?.[name]?.results;
    const endpointPath = `endpoint/${name}`;

    const availableModels = endpoint?.data?.endpoint?.[name]?.model?.available || [];
    const firstFrame = results?.first_frame ?? 0;
    const graphs = Object.entries(results ?? {}).flatMap<InferenceGraph>(([graphId, value]) => {
      // Skip first_frame and most_recent_frame, everything else is results to display
      if (typeof value === 'number') return [];

      const graph = value as InferencingEndpointResultTypes;
      if (graph.type === 'bitmap') {
        return [{ graphId, graph, series: [] }];
      }

      const series = Object.entries(graph.results ?? {});
      return series.length > 0 ? [{ graphId, graph, series }] : [];
    });
 
    return (

        <TitleCard title={`${name} Inference Details`}>
          <Row className='mb-3'>
            <Col>
              <Row className="mb-3">
                Details
                <Col xs={4}>
                  <FloatingLabel label="Select model">
                    <EndpointSelect
                      endpoint={endpoint}
                      fullpath={`${endpointPath}/model/select`}
                      style={floatingInputStyle}
                      value={endpoint?.data?.endpoint?.[name]?.model?.display_name || ''}
                    >
                      {availableModels.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </EndpointSelect>
                  </FloatingLabel>
                </Col>
              </Row>
              <Row className='mt-3'>
                  Preprocessing (e.g. flatfield)
              </Row>
              <Row className="mt-3">
                <Col xs={4}>
                  <FloatingLabel label="Mean inference time (ms)">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNull(datapath?.stats?.mean_infer_ms)}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel label="Total frames seen">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNullNoDp(datapath?.stats?.frames_seen)}
                    />
                  </FloatingLabel>
                </Col>
              </Row>
            </Col>
          </Row>
          <Row className="g-3">
            {graphs.map(({ graphId, graph, series }) => (
              <Col key={graphId} xs={12} xl={6}>
                {graph.type === 'bitmap' ? (
                  <BitmapImage
                    endpoint_url={endpoint_url}
                    endpoint_name={name}
                    graph_name={graphId}
                    alt={`${graph.graph_label || graphId} frame ${graph.frame_number ?? ''}`}
                  />
                ) : (
                  <MonitorGraph
                    endpoint={endpoint}
                    title={graph.graph_label || graphId}
                    plotTitle={graph.graph_label || graphId}
                    paths={series.map(([traceId]) =>
                      `${endpointPath}/results/${graphId}/results/${traceId}/data`)}
                    seriesNames={series.map(([traceId, trace]) => trace.label || traceId)}
                    xData={series.length > 0
                      ? Array.from(series[0][1].data, (_, index) => firstFrame + index)
                      : undefined}
                    xLabel={graph.x_label}
                    yLabel={graph.y_label}
                    axisLimit={graph.axis_limit}
                    type={graph.type}
                    showTitleCard={false}
                  />
                )}
              </Col>
            ))}
          </Row>
        </TitleCard>
    )
}

export default InferencingCard;

