import type { InferenceEndpointTypes } from '../../EndpointTypes';

import { Row, Col, Form, FloatingLabel } from 'react-bootstrap';
import { useAdapterEndpoint, EndpointButton, TitleCard } from 'odin-react';
import { useState, useMemo } from 'react';

import MonitorGraph from '../furnace/MonitorGraph';
import { checkNull, checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

interface InferenceCardProps {
  endpoint_url: string;
  name: string;
}

function InferenceCard(props: InferenceCardProps) {
    const {endpoint_url, name} = props;
 
    const inferenceEndPoint = useAdapterEndpoint<InferenceEndpointTypes>('inference', endpoint_url, 1000);
    const inferenceResults = inferenceEndPoint?.data?.[name]?.results;

    const [flatfieldNum, setFlatfieldNum] = useState(0);
    const handleFlatfieldNumChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFlatfieldNum(Number(e.target.value));
    };

    const fullpaths = useMemo(() => [
      `${name}/probabilities/columnar`,
      `${name}/probabilities/equiaxed`,
      `${name}/probabilities/alpha`,
      `${name}/probabilities/beta`,
      `${name}/probabilities/hot_tear`
    ], [name])

    return (

        <TitleCard title={`${name} Inference Details`}>
          <Row className='mb-3'>
            <Col>
              <Row className="mb-3">
                <Col xs={4}>
                  <FloatingLabel label="# Predictions">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNullNoDp(inferenceResults?.num_predictions)}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel label="Last Frame #">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNullNoDp(inferenceResults?.last_frame_number)}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                <FloatingLabel label="Avg Inf. Time">
                  <Form.Control
                    plaintext
                    readOnly
                    style={floatingLabelStyle}
                    value={checkNull(inferenceResults?.avg_inference_time_ms)}
                  />
                </FloatingLabel>
                </Col>
              </Row>
              <Row className='mt-3'>
                  <Col xs={3}/>
                  <Col>
                    <FloatingLabel label="Flatfield Acquisition #">
                      <Form.Control
                        style={floatingInputStyle}
                        type="number"
                        value={inferenceResults?.flatfield_file}
                        onChange={handleFlatfieldNumChange}
                      />
                    </FloatingLabel>
                  </Col>
                  <Col>
                    <Row>
                      <EndpointButton
                        endpoint={inferenceEndPoint}
                        fullpath={`${name}/results/set_flatfield_num`}
                        value={flatfieldNum}>
                        Set flatfield from acquisition
                      </EndpointButton>
                    </Row>
                  <Row>
                    <EndpointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={-1 /*Special case adapter-side,*/} 
                      variant='danger'
                    >
                        Clear flatfield
                    </EndpointButton>
                  </Row>
                </Col>
              </Row>
              <Row className="mt-3 justify-content-center">
                <Col xs={0} sm={1} md={2}/>
                <Col>
                  <FloatingLabel label="Active classes">
                    <Form.Control
                      readOnly
                      plaintext
                      value={inferenceEndPoint?.data?.[name]?.results?.experiment_number || 'N/A'}
                      style={{
                          border: '1px solid lightgreen',
                          backgroundColor: '#e0ffe2ff',
                          borderRadius: '0.375rem'
                      }}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={0} sm={1} md={2}/>
              </Row>
            </Col>
          </Row>
          <Row>
            <MonitorGraph
              title="Results"
              endpoint={inferenceEndPoint}
              paths={fullpaths}
              seriesNames={['col', 'equi', 'alpha', 'beta', 'tear']}
            />
          </Row>
        </TitleCard>
    )
}

export default InferenceCard;

